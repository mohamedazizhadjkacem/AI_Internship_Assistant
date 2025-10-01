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
from views.settings_view import show_settings_page

st.set_page_config(page_title="AI Internship Assistant", layout="wide")

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
    'password_recovery_mode': False,  # Track if in password recovery
    'recovery_checked': False  # Track if we've checked for recovery
}

# Initialize any missing session state variables with defaults
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# Check for password recovery flow
def check_password_recovery():
    """Check if user came from password reset email and handle accordingly."""
    try:
        # Get URL parameters
        query_params = st.query_params
        
        # Check if this is a password recovery callback
        if 'type' in query_params and query_params['type'] == 'recovery':
            # User clicked password reset link
            st.session_state.page = 'SetNewPassword'
            st.session_state.password_recovery_mode = True
            
            # Try to get the current user (should be auto-signed in by Supabase)
            try:
                current_user = db.client.auth.get_user()
                if current_user and current_user.user:
                    st.session_state.recovery_user_id = current_user.user.id
                    st.session_state.recovery_email = current_user.user.email
            except:
                # If we can't get user, redirect to login with error
                st.session_state.page = 'Login'
                st.session_state.password_recovery_error = "Password reset session expired. Please try again."
            
            return True
            
    except Exception as e:
        print(f"Error checking password recovery: {e}")
        
    return False

# Check for password recovery on app load
if not hasattr(st.session_state, 'recovery_checked'):
    st.session_state.recovery_checked = True
    check_password_recovery()

# --- HANDLER FUNCTIONS ---
def handle_login(email, password):
    if not email or not password:
        st.error("Please enter both email and password.")
        return
    result = db.sign_in_user(email, password)
    if "error" not in result:
        st.session_state.logged_in = True
        st.session_state.user_session = result['session']
        st.session_state.user_id = result['session'].user.id
        profile = db.get_user_profile()
        st.session_state.username = profile.get('username', email) if profile else email
        # Load internships after successful login
        load_internships()
        st.success("Logged in successfully!")
        time.sleep(1)
        st.rerun()
    else:
        st.error(result["error"])

def handle_register(email, password, confirm_password, username, telegram_bot_token, telegram_chat_id):
    if password != confirm_password:
        st.error("Passwords do not match.")
        return
    if not all([email, password, confirm_password, username, telegram_bot_token, telegram_chat_id]):
        st.error("Please fill in all fields.")
        return
    result = db.sign_up_user(email, password, username, telegram_bot_token, telegram_chat_id)
    if "error" not in result:
        st.success("Registration successful! Please check your email to confirm your account and then login.")
        st.session_state.page = 'Login'
        time.sleep(2)
        st.rerun()
    else:
        st.error(result["error"])

# --- UI RENDERING ---

# --- LOGIN/REGISTRATION VIEW ---
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1, 1.5, 1])

    with col2:
        if st.session_state.page == 'Login':
            st.header("Welcome Back!")
            
            # Show success message if user just reset password
            if hasattr(st.session_state, 'password_reset_success') and st.session_state.password_reset_success:
                st.success("🎉 Password reset successfully! Please log in with your new password.")
                del st.session_state.password_reset_success
            
            # Show error if recovery failed
            if hasattr(st.session_state, 'password_recovery_error'):
                st.error(st.session_state.password_recovery_error)
                del st.session_state.password_recovery_error
            
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="Enter your email")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submitted = st.form_submit_button("Login", use_container_width=True)
                if submitted:
                    handle_login(email, password)
            
            # Login page buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Don't have an account? Register", use_container_width=True):
                    st.session_state.page = 'Register'
                    st.rerun()
            
            with col2:
                if st.button("🔑 Forgot Password?", use_container_width=True, type="secondary"):
                    st.session_state.page = 'ForgotPassword'
                    st.rerun()

        elif st.session_state.page == 'Register':
            st.header("Create an Account")
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

            if st.button("Already have an account? Login", use_container_width=True):
                st.session_state.page = 'Login'
                st.rerun()

        elif st.session_state.page == 'ForgotPassword':
            from views.settings_view import show_forgot_password_form
            show_forgot_password_form()

        elif st.session_state.page == 'SetNewPassword':
            from views.settings_view import show_set_new_password_form
            show_set_new_password_form()

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
        "Settings": {"icon": "⚙️", "function": show_settings_page},
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