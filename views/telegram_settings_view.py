import streamlit as st
from supabase_db import SupabaseDB

def show_telegram_settings_page():
    st.header("🔧 Telegram Settings")
    db = SupabaseDB()
    user_id = st.session_state.get('user_id')
    if not user_id:
        st.error("You must be logged in to view this page.")
        return

    # Fetch current profile
    profile = db.get_user_profile()
    telegram_bot_token = profile.get('telegram_bot_token', '') if profile else ''
    telegram_chat_id = profile.get('telegram_chat_id', '') if profile else ''

    with st.form("telegram_settings_form"):
        new_bot_token = st.text_input("Telegram Bot Token", value=telegram_bot_token)
        new_chat_id = st.text_input("Telegram Chat ID", value=telegram_chat_id)
        submitted = st.form_submit_button("Update Telegram Settings")
        if submitted:
            success = db.update_telegram_config(user_id, new_bot_token, new_chat_id)
            if success:
                st.success("Telegram settings updated successfully!")
            else:
                st.error("Failed to update Telegram settings. Please try again.")
