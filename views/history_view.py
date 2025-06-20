import streamlit as st
import pandas as pd
from supabase_db import SupabaseDB

def show_history_page():
    """Renders the main content of the application history page.""" 
    st.title("📜 Application History")

    try:
        db = SupabaseDB()
        user_id = st.session_state.get('user_id')
        if not user_id:
            st.error("User not identified. Please log in again.")
            st.stop()

        st.write("Here is a log of all your past application activities.")
        all_internships = db.get_internships_by_user(user_id)

    except Exception as e:
        st.error(f"Failed to load data: {e}")
        st.stop()

    if all_internships:
        history = [i for i in all_internships if i.get('status') != 'pending_review']
        
        if history:
            df = pd.DataFrame(history)
            display_df = df[['created_at', 'job_title', 'company_name', 'status', 'application_link']]
            display_df = display_df.rename(columns={
                'created_at': 'Date',
                'job_title': 'Job Title',
                'company_name': 'Company',
                'status': 'Action Taken',
                'application_link': 'Original Link'
            })
            display_df['Date'] = pd.to_datetime(display_df['Date']).dt.strftime('%Y-%m-%d %H:%M')
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("No actions have been taken yet. Head to the dashboard to review applications.")
    else:
        st.info("No application history found.")
