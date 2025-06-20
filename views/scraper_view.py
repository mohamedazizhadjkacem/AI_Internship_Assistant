import streamlit as st
from supabase_db import SupabaseDB
from web_scraper import scrape_linkedin
import asyncio
import threading
import time
from datetime import datetime
from notifications import send_telegram_notification
from config import SCRAPING_INTERVAL_MINUTES


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

            # Scrape LinkedIn
            result = scrape_linkedin(job_title, location, True)  # Only last 24h
            print(f"[DEBUG] Scraped {len(result) if isinstance(result, list) else 0} internships from LinkedIn.")

            if isinstance(result, list):
                new_internships = []
                for internship in result:
                    link = internship["application_link"]
                    if link not in existing_links:
                        save_data = {
                            **internship,
                            "status": "new",
                        }
                        resp = db.add_internship(user_id, save_data)
                        if resp.get("success"):
                            new_internships.append(internship)
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
            location = st.text_input("Location", placeholder="e.g. United States", value="United States", key="scraper_location")
        with col3:
            last_24_hours = st.checkbox("Last 24h only", key="scraper_last24")

        submitted = st.form_submit_button("Search", type="primary")

    # Always keep the latest job_title and location in session state
    if job_title:
        st.session_state['last_job_title'] = job_title
    if location:
        st.session_state['last_location'] = location

    # Continuous Search Controls
    user_id = st.session_state.get('user_id')
    # Use session state for job_title/location for continuous search
    last_job_title = st.session_state.get('last_job_title', '')
    last_location = st.session_state.get('last_location', 'United States')
    if user_id:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"Continuous search will check for new internships every {SCRAPING_INTERVAL_MINUTES} minutes.")
        with col2:
            if not st.session_state.continuous_search_active:
                if st.button("Start Continuous Search", type="primary", use_container_width=True):
                    if not last_job_title:
                        st.error("Please enter a job title first (in the form above).")
                    else:
                        # --- Run a manual search first (same as 'Search' button) ---
                        with st.spinner("Scraping LinkedIn. Please wait..."):
                            result = scrape_linkedin(last_job_title, last_location, last_24_hours)

                        if isinstance(result, dict) and result.get("error"):
                            st.error(result["error"])
                            return

                        if not result:
                            st.warning("No internships found. Try adjusting your search criteria.")
                        else:
                            # --- Process and Save Results ---
                            all_internships = st.session_state.get('all_internships', [])
                            existing_links = {internship['application_link'] for internship in all_internships}
                            db = SupabaseDB()
                            new_internships_count = 0
                            duplicate_count = 0
                            for internship in result:
                                link = internship["application_link"]
                                if link not in existing_links:
                                    save_data = {
                                        **internship,
                                        "status": "new",
                                    }
                                    resp = db.add_internship(user_id, save_data)
                                    if resp.get("success"):
                                        new_internships_count += 1
                                    elif resp.get("error") == "duplicate":
                                        duplicate_count += 1
                            st.session_state.all_internships = None
                            if new_internships_count > 0:
                                st.success(f"✨ Added {new_internships_count} new internships! Check your dashboard to review them.")
                            else:
                                if duplicate_count > 0:
                                    st.info("All found internships were already in your dashboard.")
                                else:
                                    st.warning("No new internships were found to add.")
                        # --- Start continuous search in background ---
                        search_thread = threading.Thread(
                            target=continuous_scraping,
                            args=(last_job_title, last_location, user_id),
                            daemon=True
                        )
                        search_thread.start()
                        st.session_state.search_thread = search_thread
                        st.session_state.continuous_search_active = True
                        st.rerun()
            else:
                if st.button("Stop Continuous Search", type="secondary", use_container_width=True):
                    st.session_state.continuous_search_active = False
                    st.session_state.search_thread = None
                    st.rerun()

    # Show continuous search status
    if st.session_state.continuous_search_active:
        st.success("🔄 Continuous search is active. You'll receive Telegram notifications for new internships.")

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
        existing_links = {internship['application_link'] for internship in all_internships}

        db = SupabaseDB()
        new_internships_count = 0
        duplicate_count = 0

        with st.spinner("Processing and saving new internships..."):
            for internship in result:
                link = internship["application_link"]
                if link not in existing_links:
                    save_data = {
                        **internship,
                        "status": "new",
                    }
                    resp = db.add_internship(user_id, save_data)
                    if resp.get("success"):
                        new_internships_count += 1
                    elif resp.get("error") == "duplicate":
                        duplicate_count += 1

        # Clear the session state to force a refresh of internships
        st.session_state.all_internships = None

        # Show results summary
        if new_internships_count > 0:
            st.success(f"✨ Added {new_internships_count} new internships! Check your dashboard to review them.")
        else:
            if duplicate_count > 0:
                st.info("All found internships were already in your dashboard.")
            else:
                st.warning("No new internships were found to add.")
