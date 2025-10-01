import streamlit as st
from supabase_db import SupabaseDB
import time

# Import views
from views.home_view import show_home_page
from views.dashboard_view import show_dashboard_page
from views.history_view import show_history_page
from views.scraper_view import show_scraper_page
from views.telegram_settings_view import show_telegram_settings_page
from views.resume_view import show_resume_page
from views.ai_generator_view import show_ai_generator_page

st.set_page_config(page_title="AI Internship Assistant", layout="wide")

# Check for email confirmation in URL parameters
query_params = st.query_params
if "confirmed" in query_params:
    if query_params["confirmed"] == "true":
        st.success("🎉 Email confirmed successfully! You can now log in with your credentials.")
        # Clear the URL parameter after showing the message
        st.query_params.clear()

# --- DATABASE INITIALIZATION ---
try:
    db = SupabaseDB()
except Exception as e:
    st.error(f"Failed to connect to the database: {e}")
    st.stop()

def load_internships():
    if st.session_state.user_id:
        print(f"Loading internships for user: {st.session_state.user_id}")  # Debug print
        internships = db.get_internships_by_user(st.session_state.user_id)
        print(f"Loaded {len(internships) if internships else 0} internships")  # Debug print
        st.session_state.all_internships = internships or []
        return internships
    return []

# --- SESSION STATE INITIALIZATION ---
# Initialize all session state variables with their default values
defaults = {
    'logged_in': False,
    'page': 'Login',
    'view': 'Home',
    'user_session': None,
    'user_id': None,
    'username': None,
    'all_internships': [],  # Always initialize as empty list, never None
    'show_details': None,
    'confirm_delete': None,
    'show_descriptions': {},
    'continuous_search_active': False,
    'search_thread': None,
    'delete_success': False,  # Add this for delete confirmation handling
    'force_refresh': False,  # Flag to force data refresh
    'registration_error': None,  # For handling registration errors outside forms
    'registration_success': False,  # For handling registration success
    'pending_confirmation_email': None,  # Track email awaiting confirmation
    'login_error': None,  # For handling login errors

}

# Initialize any missing session state variables with defaults
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value



# --- HANDLER FUNCTIONS ---
def handle_login(email, password):
    if not email or not password:
        st.session_state.login_error = "Please enter both email and password."
        return
    
    with st.spinner("Signing you in..."):
        result = db.sign_in_user(email, password)
    
    if "error" not in result:
        st.session_state.logged_in = True
        st.session_state.user_session = result['session']
        st.session_state.user_id = result['session'].user.id
        profile = db.get_user_profile()
        st.session_state.username = profile.get('username', email) if profile else email
        st.session_state.login_error = None  # Clear any login errors
        # Load internships after successful login
        load_internships()
        st.success("Logged in successfully!")
        time.sleep(1)
        st.rerun()
    else:
        error_msg = result["error"]
        if "confirm your email" in error_msg.lower():
            st.session_state.login_error = error_msg
            st.session_state.pending_confirmation_email = email
        else:
            st.session_state.login_error = error_msg
            st.session_state.pending_confirmation_email = None

def handle_register(email, password, confirm_password, username, telegram_bot_token, telegram_chat_id):
    # Validation checks
    if password != confirm_password:
        st.session_state.registration_error = "Passwords do not match."
        return False
    if not all([email, password, confirm_password, username, telegram_bot_token, telegram_chat_id]):
        st.session_state.registration_error = "Please fill in all fields."
        return False
    
    # Show loading message for user feedback
    with st.spinner("Creating your account..."):
        result = db.sign_up_user(email, password, username, telegram_bot_token, telegram_chat_id)
    
    if "error" not in result:
        st.session_state.registration_success = True
        st.session_state.registration_error = None
        st.session_state.pending_confirmation_email = email  # Track email for confirmation
        return True
    else:
        error_msg = result["error"]
        # Store user-friendly error messages in session state
        if "Account creation conflict detected" in error_msg:
            st.session_state.registration_error = "⚠️ There was a conflict creating your account. This might be due to a previous incomplete registration. Please try again in a few moments, or contact support if the problem persists."
        elif "already registered" in error_msg.lower():
            st.session_state.registration_error = "📧 This email is already registered. Please try logging in instead, or use a different email address."
        else:
            st.session_state.registration_error = f"❌ Registration failed: {error_msg}"
        return False

# --- UI RENDERING ---

# --- LOGIN/REGISTRATION VIEW ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        if st.session_state.page == 'Login':
            st.header("Welcome Back!")
            

            

            

      

            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    handle_login(email, password)
            
            # Handle login errors outside the form
            if getattr(st.session_state, 'login_error', None):
                st.error(st.session_state.login_error)
                
                # If email confirmation is pending, show resend option
                pending_email = getattr(st.session_state, 'pending_confirmation_email', None)
                if pending_email and "confirm your email" in st.session_state.login_error.lower():
                    st.info("💡 **Haven't received the confirmation email?**")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📧 Resend Confirmation Email", key="resend_confirmation"):
                            with st.spinner("Resending confirmation email..."):
                                resend_result = db.resend_confirmation_email(pending_email)
                            if "success" in resend_result:
                                st.success("✅ Confirmation email sent! Please check your inbox.")
                                st.session_state.login_error = None
                            else:
                                st.error(f"❌ Failed to resend email: {resend_result.get('error', 'Unknown error')}")
                    with col2:
                        if st.button("🔄 Try Login Again", key="retry_login"):
                            st.session_state.login_error = None
                            st.session_state.pending_confirmation_email = None
                            st.rerun()
            
            # Login page buttons - show only if no error or error is not email-related
            if not getattr(st.session_state, 'login_error', None) or "confirm your email" not in getattr(st.session_state, 'login_error', '').lower():
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Don't have an account? Register", use_container_width=True):
                        st.session_state.page = 'Register'
                        st.session_state.login_error = None
                        st.rerun()
            
        elif st.session_state.page == 'Register':
            st.header("Create an Account")
            
            # Handle registration success
            if getattr(st.session_state, 'registration_success', False):
                st.success("🎉 **Registration successful!**")
                st.info("""
                📧 **Next Steps:**
                1. Check your email inbox (and spam folder)
                2. Click the confirmation link in the email
                3. Return here and log in with your credentials
                
                💡 The confirmation email may take a few minutes to arrive.
                """)
                
                # Add button to go to login
                if st.button("📝 Go to Login Page", use_container_width=True):
                    st.session_state.page = 'Login'
                    st.session_state.registration_success = False
                    st.rerun()
                
                # Don't auto-redirect, let user read the instructions
                st.stop()
            
            # Registration form
            with st.form("register_form"):
                username = st.text_input("Username", placeholder="Choose a username")
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Create a password")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
                telegram_bot_token = st.text_input("Telegram Bot Token", placeholder="Enter your Telegram Bot Token")
                telegram_chat_id = st.text_input("Telegram Chat ID", placeholder="Enter your Telegram Chat ID")
                submitted = st.form_submit_button("Register", use_container_width=True)
                if submitted:
                    handle_register(email, password, confirm_password, username, telegram_bot_token, telegram_chat_id)
            
            # Handle registration errors outside the form
            if getattr(st.session_state, 'registration_error', None):
                st.error(st.session_state.registration_error)
                
                # Provide helpful action buttons outside the form
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 Try Again", key="retry_register"):
                        st.session_state.registration_error = None
                        st.rerun()
                with col2:
                    if st.button("🔙 Back to Login", key="back_to_login"):
                        st.session_state.page = 'Login'
                        st.session_state.registration_error = None
                        st.rerun()
            else:
                # Show login link only if no error
                if st.button("Already have an account? Login", use_container_width=True):
                    st.session_state.page = 'Login'
                    st.rerun()



# --- MAIN APPLICATION VIEW ---
else:
    # --- SIDEBAR NAVIGATION ---
    st.sidebar.success(f"Welcome, {st.session_state.get('username', 'User')}!")
    
    PAGES = {
        "Home": {"icon": "🏠", "function": show_home_page},
        "Dashboard": {"icon": "📊", "function": show_dashboard_page},
        "Run Scrapper": {"icon": "⚙️", "function": show_scraper_page},
        "AI Content Generator": {"icon": "🤖", "function": show_ai_generator_page},
        "Resume Manager": {"icon": "📄", "function": show_resume_page},
        "Telegram Settings": {"icon": "🔧", "function": show_telegram_settings_page},
        "Application History": {"icon": "📋", "function": show_history_page}
    }

    st.sidebar.title("Choose page")
    
    # Create buttons for each page
    for page_name, page_info in PAGES.items():
        # Use a different type for the selected button to make it look active
        button_type = "primary" if st.session_state.view == page_name else "secondary"
        if st.sidebar.button(f"{page_info['icon']} {page_name}", use_container_width=True, type=button_type):
            st.session_state.view = page_name
            st.rerun()

    # Logout button at the bottom
    st.sidebar.write("---")
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.page = 'Login'
        # Clear session state on logout
        for key in list(st.session_state.keys()):
            if key not in ['page']:
                del st.session_state[key]
        st.rerun()

    # --- CENTRALIZED DATA LOADER ---            # This ensures that the main internship data is always loaded and consistent
    def ensure_data_loaded():
        """Loads internships from database if needed."""
        # Always initialize all_internships as an empty list if it doesn't exist or is None
        if 'all_internships' not in st.session_state or st.session_state.get('all_internships') is None:
            st.session_state['all_internships'] = []

        current_internships = st.session_state.get('all_internships', [])
        
        # Load internships if user is logged in and list is empty
        if st.session_state.get('logged_in') and not current_internships:
            user_id = st.session_state.get('user_id')
            
            if not user_id:
                st.error("No user ID found in session. Please try logging in again.")
                return False

            try:
                with st.spinner("Loading internships..."):
                    internships = db.get_internships_by_user(user_id)
                    
                    # Ensure internships is always a list
                    if internships is None:
                        internships = []
                    elif not isinstance(internships, list):
                        internships = list(internships) if hasattr(internships, '__iter__') else []
                    
                    st.session_state['all_internships'] = internships
                    print(f"[DEBUG] Loaded {len(internships)} internships for user {user_id}")
                    return True
            except Exception as e:
                st.error(f"Error loading internships: {str(e)}")
                st.session_state.all_internships = []
                return False
        return True

    # Load data when needed - always check for Dashboard, when data is missing/None, or when explicit refresh is requested
    if (st.session_state.view == 'Dashboard' or 
        not st.session_state.get('all_internships') or 
        st.session_state.get('all_internships') is None or 
        st.session_state.get('force_refresh', False)):
        
        # Clear the force refresh flag
        if st.session_state.get('force_refresh', False):
            st.session_state['force_refresh'] = False
            st.session_state['all_internships'] = None  # Ensure data is reloaded
            
        ensure_data_loaded()

    # --- RENDER SELECTED PAGE ---
    # Use st.session_state.view to render the correct page. Default to Home.
    page_to_render = st.session_state.get('view', 'Home')
    page = PAGES[page_to_render]
    page["function"]()