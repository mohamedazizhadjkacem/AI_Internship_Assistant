import streamlit as st

def show_home_page():
    """Renders the main content of the home page."""
    st.title(f"🤖 Welcome to your AI Internship Assistant, {st.session_state.get('username', 'User')}!")
    st.markdown("---")
    st.markdown(
        """
        This tool helps you automate and manage your internship application process.

        **👈 Select an option from the sidebar** to get started:

     
        - **📊 Dashboard**: View and manage all your saved internships.
        - **📜 Application History**: See a log of all your past applications.
        """
    )
