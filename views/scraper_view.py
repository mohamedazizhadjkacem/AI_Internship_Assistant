import streamlit as st
from supabase_db import SupabaseDB
from web_scraper import scrape_linkedin
import asyncio
import threading
import time
from datetime import datetime
from notifications import send_telegram_notification
from config import SCRAPING_INTERVAL_MINUTES


def process_and_save_search_results(result, user_id, all_internships):
    """Helper function to process and save search results with comprehensive duplicate detection"""
    print(f"[DEBUG] Processing {len(result)} scraped internships")
    print(f"[DEBUG] Current user has {len(all_internships)} existing internships")
    
    db = SupabaseDB()
    new_internships_count = 0
    duplicate_count = 0
    
    for i, internship in enumerate(result):
        print(f"[DEBUG] Processing internship {i+1}: {internship.get('job_title', 'Unknown')} at {internship.get('company_name', 'Unknown')}")
        
        save_data = {
            **internship,
            "status": "new",
        }
        
        # Use improved duplicate checking from database
        resp = db.add_internship(user_id, save_data)
        print(f"[DEBUG] Save response: {resp}")
        
        if resp.get("success"):
            new_internships_count += 1
            print(f"[DEBUG] Successfully saved new internship {new_internships_count}")
        elif resp.get("error") == "duplicate":
            duplicate_count += 1
            reason = resp.get("message", "unknown reason")
            print(f"[DEBUG] Duplicate internship detected: {reason}")
        else:
            error_msg = resp.get("error", "unknown error")
            print(f"[DEBUG] Failed to save internship: {error_msg}")
    
    print(f"[DEBUG] Final results: {new_internships_count} new, {duplicate_count} duplicates")
    return new_internships_count, duplicate_count


def continuous_scraping(job_title, location, user_id):
    """Background task to continuously scrape LinkedIn for new internships."""
    db = SupabaseDB()
    
    # Temporarily skip notification field initialization until database is updated
    # print(f"[DEBUG] Initializing notification field for user {user_id}")
    # init_result = db.initialize_notification_field(user_id)
    # print(f"[DEBUG] Notification field initialization result: {init_result}")
    
    # Fetch user's Telegram config once at the start
    user_profile = db.get_user_profile(user_id)
    telegram_bot_token = user_profile.get('telegram_bot_token')
    telegram_chat_id = user_profile.get('telegram_chat_id')
    print(f"[DEBUG] Telegram config for user {user_id}: token={telegram_bot_token}, chat_id={telegram_chat_id}")

    while True:
        try:
            # Get current internships count for logging
            all_internships = db.get_internships_by_user(user_id)
            print(f"[DEBUG] Continuous: Found {len(all_internships) if all_internships else 0} existing internships in database")

            # Scrape LinkedIn
            result = scrape_linkedin(job_title, location, True)  # Only last 24h
            print(f"[DEBUG] Scraped {len(result) if isinstance(result, list) else 0} internships from LinkedIn.")

            newly_saved_internships = []
            if isinstance(result, list):
                for internship in result:
                    print(f"[DEBUG] Continuous: Processing internship: {internship.get('job_title', 'Unknown')} at {internship.get('company_name', 'Unknown')}")
                    
                    save_data = {
                        **internship,
                        "status": "new"
                    }
                    
                    resp = db.add_internship(user_id, save_data)
                    print(f"[DEBUG] Continuous: Save response: {resp}")
                    
                    if resp.get("success"):
                        # Add the internship ID to the data for notification tracking
                        internship_with_id = {**internship, 'id': resp['data']['id']}
                        newly_saved_internships.append(internship_with_id)
                        print(f"[DEBUG] Continuous: Successfully saved internship with ID {resp['data']['id']}")
                    elif resp.get("error") == "duplicate":
                        print(f"[DEBUG] Continuous: Duplicate internship detected: {resp.get('message', 'unknown reason')}")
                    else:
                        print(f"[DEBUG] Continuous: Failed to save internship: {resp}")
                        
            # Only notify about newly saved internships since duplicates are filtered out
            internships_to_notify = newly_saved_internships
            print(f"[DEBUG] Total internships to notify: {len(internships_to_notify)} newly saved internships")

            # Send notifications if there are internships to notify about
            if internships_to_notify and telegram_bot_token and telegram_chat_id:
                successfully_notified = []
                
                # Send individual detailed messages for each internship
                for internship in internships_to_notify:
                        detail_message = (
                            f"✨ New Internship: {internship['job_title']}\n"
                            f"🏢 Company: {internship['company_name']}\n"
                            f"🔗 Apply Here ({internship['application_link']})\n\n"
                            f"LinkedIn ({internship['application_link']})\n"
                            f"{internship['company_name']} hiring {internship['job_title']}\n"
                            f"{internship.get('job_description', '').split('Posted')[0]}"
                        )
                        try:
                            print(f"[DEBUG] Sending Telegram notification for internship: {internship['job_title']} at {internship['company_name']}")
                            send_telegram_notification(detail_message, telegram_bot_token, telegram_chat_id)
                            successfully_notified.append(internship)
                            print(f"[DEBUG] Successfully sent notification for internship ID: {internship.get('id', 'unknown')}")
                        except Exception as notify_err:
                            print(f"[ERROR] Failed to send Telegram notification: {notify_err}")
                
                # Send summary message only if notifications were successful
                if successfully_notified:
                    summary = f"🎯 Sent {len(successfully_notified)} internship notifications!\n\n"
                    for idx, internship in enumerate(successfully_notified, 1):
                        summary += f"{idx}. {internship['job_title']} at {internship['company_name']}\n"
                    try:
                        print(f"[DEBUG] Sending Telegram summary notification")
                        send_telegram_notification(summary, telegram_bot_token, telegram_chat_id)
                    except Exception as notify_err:
                        print(f"[ERROR] Failed to send Telegram summary notification: {notify_err}")
                        
            elif not internships_to_notify:
                print(f"[DEBUG] No new internships to notify for user {user_id}.")
            elif not (telegram_bot_token and telegram_chat_id):
                print(f"[ERROR] Telegram config missing for user {user_id}.")

        except Exception as e:
            print(f"Error in continuous scraping: {e}")

        # Wait for the specified interval
        time.sleep(SCRAPING_INTERVAL_MINUTES * 60)


def show_scraper_page():
    """Renders the LinkedIn scraper page allowing users to search and save internships."""

    st.title("⚙️ Internship Scraper")
    st.markdown("Search LinkedIn for the latest internship opportunities and save them to your dashboard.")
    st.markdown("---")

    # Initialize continuous search state
    if 'continuous_search_active' not in st.session_state:
        st.session_state.continuous_search_active = False
        st.session_state.search_thread = None

    # --- Search Form ---
    with st.form("scraper_form", clear_on_submit=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            job_title = st.text_input("Job Title", placeholder="e.g. Software Engineer Intern", 
                                    value=st.session_state.get('last_job_title', ''), key="scraper_job_title")
        with col2:
            location = st.text_input("Location (Optional)", placeholder="Leave empty for global search", 
                                   value=st.session_state.get('last_location', ''), key="scraper_location")
        with col3:
            last_24_hours = st.checkbox("Last 24h only", key="scraper_last24")

        # Form buttons
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("Search", type="primary", use_container_width=True)
        with col2:
            user_id = st.session_state.get('user_id')
            if user_id and not st.session_state.get('continuous_search_active', False):
                continuous_search_submitted = st.form_submit_button("Start Continuous Search", type="secondary", use_container_width=True)
            else:
                continuous_search_submitted = False

    # Always keep the latest job_title and location in session state
    if job_title:
        st.session_state['last_job_title'] = job_title
    # Store location as-is, including empty string for global search
    st.session_state['last_location'] = location

    # Show continuous search status
    user_id = st.session_state.get('user_id')
    if user_id:
        if st.session_state.get('continuous_search_active', False):
            search_location = st.session_state.get('last_location', '')
            location_text = f" in {search_location}" if search_location else " globally"
            st.success(f"🔄 Continuous search is active! Monitoring for new '{st.session_state.get('last_job_title', 'internships')}' opportunities{location_text} every {SCRAPING_INTERVAL_MINUTES} minutes.")
        else:
            st.info(f"ℹ️ Fill in the job title above and optionally specify a location (or leave empty for global search), then click 'Start Continuous Search' to begin automated monitoring every {SCRAPING_INTERVAL_MINUTES} minutes.")
    # Handle continuous search form submission
    if continuous_search_submitted:
        print(f"[DEBUG] Continuous search form values - job_title: '{job_title}', location: '{location}'")
        
        if not job_title or job_title.strip() == '':
            st.error("Please enter a job title to start continuous search.")
        else:
            # First, perform the search automatically
            search_location = location.strip() if location else None
            location_display = search_location if search_location else "globally"
            
            with st.spinner(f"Performing initial search {location_display}..."):
                # Perform the scraping first - pass None for global search
                result = scrape_linkedin(job_title, search_location, last_24_hours)
                
                # Check for errors (result is a dict with "error" key)
                if isinstance(result, dict) and result.get("error"):
                    st.error(result["error"])
                else:
                    # Check if we got results (result is a list of internships)
                    if not result:
                        st.warning("No internships found. Try adjusting your search criteria.")
                    else:
                        # Get current internships to check for duplicates
                        all_internships = st.session_state.get('all_internships', [])
                        
                        # Process and save the results
                        new_internships, duplicate_internships = process_and_save_search_results(
                            result, user_id, all_internships
                        )
                        
                        if new_internships > 0 or duplicate_internships > 0:
                            st.success(f"✅ Found {new_internships} new internships and {duplicate_internships} duplicates!")
                            # Force refresh the data to show new results
                            st.session_state.force_refresh = True
                        else:
                            st.info("No new internships found in this search.")
                    
                    # Then start continuous search regardless of results
                    st.session_state.continuous_search_active = True
                    st.session_state.last_job_title = job_title
                    st.session_state.last_location = location
                    
                    # Start the background thread for continuous searching
                    search_thread = threading.Thread(
                        target=continuous_scraping,
                        args=(job_title, search_location, user_id),
                        daemon=True
                    )
                    search_thread.start()
                    st.session_state.search_thread = search_thread
                    
                    st.success(f"🔄 Continuous search started! Monitoring for '{job_title}' {location_display} every {SCRAPING_INTERVAL_MINUTES} minutes.")
                    st.rerun()

    # Stop continuous search button (outside form)
    if st.session_state.get('continuous_search_active', False):
        if st.button("Stop Continuous Search", type="secondary", use_container_width=True):
            st.session_state.continuous_search_active = False
            st.session_state.search_thread = None
            st.success("� Continuous search stopped.")
            st.rerun()
        # Clear the trigger flag
        st.session_state.trigger_search = False

    if submitted:
        if not job_title:
            st.warning("Please enter a job title to search.")
            st.stop()
        # Store the latest search in session state for continuous search
        st.session_state['last_job_title'] = job_title
        st.session_state['last_location'] = location

        # Handle global search when location is empty
        search_location = location.strip() if location else None
        location_display = f" in {search_location}" if search_location else " globally"
        
        with st.spinner(f"Scraping LinkedIn{location_display}. Please wait..."):
            result = scrape_linkedin(job_title, search_location, last_24_hours)

        if isinstance(result, dict) and result.get("error"):
            st.error(result["error"])
            return

        if not result:
            st.warning("No internships found. Try adjusting your search criteria.")
            return

        # --- Process and Save Results ---
        user_id = st.session_state.get("user_id")
        all_internships = st.session_state.get('all_internships', [])

        with st.spinner("Processing and saving new internships..."):
            new_internships_count, duplicate_count = process_and_save_search_results(result, user_id, all_internships)

        # Clear the session state to force a refresh of internships
        st.session_state.all_internships = None
        st.session_state['force_refresh'] = True  # Add explicit refresh flag

        # Show results summary
        if new_internships_count > 0:
            st.success(f"✨ Added {new_internships_count} new internships! Check your dashboard to review them.")
        else:
            if duplicate_count > 0:
                st.info("All found internships were already in your dashboard.")
            else:
                st.warning("No new internships were found to add.")
        
        # Check if we need to start continuous search after this search
        if st.session_state.get('start_continuous_after_search', False):
            st.session_state.start_continuous_after_search = False
            # Start continuous search in background
            search_thread = threading.Thread(
                target=continuous_scraping,
                args=(job_title, location, user_id),
                daemon=True
            )
            search_thread.start()
            st.session_state.search_thread = search_thread
            st.session_state.continuous_search_active = True
            st.success("🔄 Continuous search started! You'll receive notifications for new internships.")
            st.rerun()
