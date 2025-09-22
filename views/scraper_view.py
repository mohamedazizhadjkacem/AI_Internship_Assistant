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
    """Helper function to process and save search results"""
    existing_links = {internship['application_link'] for internship in all_internships}
    
    print(f"[DEBUG] Found {len(all_internships)} existing internships in session state")
    print(f"[DEBUG] Existing links: {list(existing_links)[:5]}...")  # Show first 5 links
    print(f"[DEBUG] Processing {len(result)} scraped internships")
    
    db = SupabaseDB()
    new_internships_count = 0
    duplicate_count = 0
    
    for i, internship in enumerate(result):
        link = internship["application_link"]
        print(f"[DEBUG] Scraped internship {i+1}: {internship.get('job_title', 'Unknown')} at {internship.get('company_name', 'Unknown')}")
        print(f"[DEBUG] Scraped link: {link}")
        if link not in existing_links:
            save_data = {
                **internship,
                "status": "new",
            }
            print(f"[DEBUG] Attempting to save internship: {internship.get('job_title', 'Unknown')} at {internship.get('company_name', 'Unknown')}")
            resp = db.add_internship(user_id, save_data)
            print(f"[DEBUG] Save response: {resp}")
            if resp.get("success"):
                new_internships_count += 1
                print(f"[DEBUG] Successfully saved internship {new_internships_count}")
            elif resp.get("error") == "duplicate":
                duplicate_count += 1
                print(f"[DEBUG] Duplicate internship detected")
            else:
                print(f"[DEBUG] Failed to save internship: {resp}")
        else:
            print(f"[DEBUG] Skipping existing internship: {internship.get('job_title', 'Unknown')}")
    
    return new_internships_count, duplicate_count


def continuous_scraping(job_title, location, user_id):
    """Background task to continuously scrape LinkedIn for new internships."""
    db = SupabaseDB()
    # Fetch user's Telegram config once at the start
    user_profile = db.get_user_profile(user_id)
    telegram_bot_token = user_profile.get('telegram_bot_token')
    telegram_chat_id = user_profile.get('telegram_chat_id')
    print(f"[DEBUG] Telegram config for user {user_id}: token={telegram_bot_token}, chat_id={telegram_chat_id}")

    while True:
        try:
            # Get current internships from database
            all_internships = db.get_internships_by_user(user_id)
            existing_links = {internship['application_link'] for internship in all_internships}
            
            print(f"[DEBUG] Continuous: Found {len(all_internships) if all_internships else 0} existing internships in database")
            print(f"[DEBUG] Continuous: Existing links: {list(existing_links)[:3]}...")  # Show first 3 links

            # Scrape LinkedIn
            result = scrape_linkedin(job_title, location, True)  # Only last 24h
            print(f"[DEBUG] Scraped {len(result) if isinstance(result, list) else 0} internships from LinkedIn.")

            if isinstance(result, list):
                new_internships = []
                for internship in result:
                    link = internship["application_link"]
                    print(f"[DEBUG] Continuous: Checking scraped link: {link}")
                    if link not in existing_links:
                        save_data = {
                            **internship,
                            "status": "new",
                        }
                        print(f"[DEBUG] Continuous: Attempting to save internship: {internship.get('job_title', 'Unknown')} at {internship.get('company_name', 'Unknown')}")
                        resp = db.add_internship(user_id, save_data)
                        print(f"[DEBUG] Continuous: Save response: {resp}")
                        if resp.get("success"):
                            new_internships.append(internship)
                            print(f"[DEBUG] Continuous: Successfully saved internship")
                        else:
                            print(f"[DEBUG] Continuous: Failed to save internship: {resp}")
                    else:
                        print(f"[DEBUG] Continuous: Skipping existing internship: {internship.get('job_title', 'Unknown')}")
                print(f"[DEBUG] Found {len(new_internships)} new internships for user {user_id}.")

                # Send notification if new internships found
                if new_internships and telegram_bot_token and telegram_chat_id:
                    # Send individual detailed messages for each internship
                    for internship in new_internships:
                        detail_message = (
                            f"✨ New Internship: {internship['job_title']}\n"
                            f"🏢 Company: {internship['company_name']}\n"
                            f"🔗 Apply Here ({internship['application_link']})\n\n"
                            f"LinkedIn ({internship['application_link']})\n"
                            f"{internship['company_name']} hiring {internship['job_title']}\n"
                            f"{internship.get('job_description', '').split('Posted')[0]}"
                        )
                        try:
                            print(f"[DEBUG] Sending Telegram notification for internship: {detail_message}")
                            send_telegram_notification(detail_message, telegram_bot_token, telegram_chat_id)
                        except Exception as notify_err:
                            print(f"[ERROR] Failed to send Telegram notification: {notify_err}")
                    # Send summary message
                    summary = f"🎯 Found {len(new_internships)} new internships!\n\n"
                    for idx, internship in enumerate(new_internships, 1):
                        summary += f"{idx}. {internship['job_title']} at {internship['company_name']}\n"
                    try:
                        print(f"[DEBUG] Sending Telegram summary notification: {summary}")
                        send_telegram_notification(summary, telegram_bot_token, telegram_chat_id)
                    except Exception as notify_err:
                        print(f"[ERROR] Failed to send Telegram summary notification: {notify_err}")
                elif not new_internships:
                    print(f"[DEBUG] No new internships found for user {user_id}.")
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
            job_title = st.text_input("Job Title", placeholder="e.g. Software Engineer Intern", key="scraper_job_title")
        with col2:
            location = st.text_input("Location", placeholder="e.g. Canada", key="scraper_location")
        with col3:
            last_24_hours = st.checkbox("Last 24h only", key="scraper_last24")

        submitted = st.form_submit_button("Search", type="primary")

    # Always keep the latest job_title and location in session state
    if job_title:
        st.session_state['last_job_title'] = job_title
    if location:
        st.session_state['last_location'] = location
    else:
        # If location is empty, set default
        if location == '':
            st.session_state['last_location'] = 'United States'

    # Continuous Search Controls
    user_id = st.session_state.get('user_id')
    
    if user_id:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"Continuous search will check for new internships every {SCRAPING_INTERVAL_MINUTES} minutes.")
        with col2:
            if not st.session_state.continuous_search_active:
                if st.button("Start Continuous Search", type="primary", use_container_width=True):
                    # Get current form values directly (they should be available here)
                    current_job_title = job_title.strip() if job_title else ''
                    current_location = location.strip() if location else 'United States'
                    current_last_24h = last_24_hours if 'last_24_hours' in locals() else True
                    
                    print(f"[DEBUG] Direct form values - job_title: '{current_job_title}', location: '{current_location}'")
                    
                    if not current_job_title:
                        st.error("Please enter a job title first (in the form above).")
                        st.info("💡 **Tip**: Make sure to type a job title in the 'Job Title' field above, then click this button.")
                    else:
                        # First, perform the search automatically (simulate clicking Search button)
                        with st.spinner("Performing initial search..."):
                            # Perform the scraping first
                            result = scrape_linkedin(current_job_title, current_location, current_last_24h)
                            
                            # Check for errors (result is a dict with "error" key)
                            if isinstance(result, dict) and result.get("error"):
                                st.error(result["error"])
                                return
                            
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
                        
                        # Then start continuous search
                        st.session_state.continuous_search_active = True
                        st.session_state.last_job_title = current_job_title
                        st.session_state.last_location = current_location
                        
                        # Start the background thread for continuous searching
                        search_thread = threading.Thread(
                            target=continuous_scraping,
                            args=(current_job_title, current_location, user_id),
                            daemon=True
                        )
                        search_thread.start()
                        st.session_state.search_thread = search_thread
                        
                        st.success(f"🔄 Continuous search started! Searching for '{current_job_title}' in '{current_location}' every {SCRAPING_INTERVAL_MINUTES} minutes.")
                        st.rerun()
            else:
                if st.button("Stop Continuous Search", type="secondary", use_container_width=True):
                    st.session_state.continuous_search_active = False
                    st.session_state.search_thread = None
                    st.rerun()

    # Show continuous search status
    if st.session_state.continuous_search_active:
        st.success("🔄 Continuous search is active. You'll receive Telegram notifications for new internships.")

    # Check if we need to trigger a search (from continuous search button)
    if st.session_state.get('trigger_search', False):
        submitted = True
        job_title = st.session_state.get('search_job_title', '')
        location = st.session_state.get('search_location', 'Canada')
        last_24_hours = st.session_state.get('search_last_24h', False)
        # Clear the trigger flag
        st.session_state.trigger_search = False

    if submitted:
        if not job_title:
            st.warning("Please enter a job title to search.")
            st.stop()
        # Store the latest search in session state for continuous search
        st.session_state['last_job_title'] = job_title
        st.session_state['last_location'] = location

        with st.spinner("Scraping LinkedIn. Please wait..."):
            result = scrape_linkedin(job_title, location, last_24_hours)

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
