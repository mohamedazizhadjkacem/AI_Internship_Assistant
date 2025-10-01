import streamlit as st
import time
from supabase_db import SupabaseDB

def show_settings_page():
    """Displays the user settings page with password management."""
    st.title("⚙️ Account Settings")
    
    # Initialize database
    db = SupabaseDB()
    
    # Get current user profile
    try:
        profile = db.get_user_profile()
        if not profile:
            st.error("Unable to load user profile. Please try logging in again.")
            return
            
        user_email = profile.get('email', 'N/A')
        username = profile.get('username', 'N/A')
        
    except Exception as e:
        st.error(f"Error loading profile: {e}")
        return

    # Profile Information Section
    st.header("👤 Profile Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Username:** {username}")
    with col2:
        st.info(f"**Email:** {user_email}")

    st.divider()

    # Change Password Section
    st.header("🔐 Change Password")
    st.markdown("Update your account password for enhanced security.")

    with st.form("change_password_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            current_password = st.text_input(
                "Current Password", 
                type="password", 
                placeholder="Enter your current password"
            )
        
        with col2:
            new_password = st.text_input(
                "New Password", 
                type="password", 
                placeholder="Enter your new password"
            )
        
        confirm_new_password = st.text_input(
            "Confirm New Password", 
            type="password", 
            placeholder="Confirm your new password"
        )
        
        # Password requirements
        st.markdown("**Password Requirements:**")
        st.markdown("- At least 8 characters long")
        st.markdown("- Contains at least one uppercase letter")
        st.markdown("- Contains at least one lowercase letter") 
        st.markdown("- Contains at least one number")
        
        submitted = st.form_submit_button("🔄 Change Password", use_container_width=True)
        
        if submitted:
            # Validation
            if not all([current_password, new_password, confirm_new_password]):
                st.error("Please fill in all password fields.")
                return
                
            if new_password != confirm_new_password:
                st.error("New passwords do not match.")
                return
                
            if len(new_password) < 8:
                st.error("New password must be at least 8 characters long.")
                return
                
            if not any(c.isupper() for c in new_password):
                st.error("New password must contain at least one uppercase letter.")
                return
                
            if not any(c.islower() for c in new_password):
                st.error("New password must contain at least one lowercase letter.")
                return
                
            if not any(c.isdigit() for c in new_password):
                st.error("New password must contain at least one number.")
                return
            
            if current_password == new_password:
                st.error("New password must be different from current password.")
                return
            
            # Attempt to change password
            try:
                with st.spinner("Changing password..."):
                    result = db.change_user_password(current_password, new_password)
                    
                if result.get("success"):
                    st.success("✅ " + result.get("message", "Password changed successfully!"))
                    st.balloons()
                else:
                    st.error("❌ " + result.get("error", "Failed to change password."))
                    
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    st.divider()

    # Account Security Section
    st.header("🛡️ Account Security")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Last Login:** Not tracked yet")
        st.markdown("**Account Status:** Active")
        
    with col2:
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            # Clear session state and redirect to login
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Signed out successfully!")
            st.rerun()

    st.divider()

    # Danger Zone
    st.header("⚠️ Danger Zone")
    
    with st.expander("🗑️ Delete Account", expanded=False):
        st.warning("**Warning:** This action cannot be undone!")
        st.markdown("Deleting your account will:")
        st.markdown("- Remove all your internship data")
        st.markdown("- Delete your profile information") 
        st.markdown("- Cancel any active subscriptions")
        
        delete_confirmation = st.text_input(
            "Type 'DELETE' to confirm account deletion:",
            placeholder="Type DELETE to confirm"
        )
        
        if st.button("🗑️ Permanently Delete Account", type="primary", disabled=(delete_confirmation != "DELETE")):
            st.error("Account deletion feature is not yet implemented for safety reasons.")
            st.info("Please contact support if you need to delete your account.")

def show_forgot_password_form():
    """Shows the forgot password form."""
    st.header("🔑 Reset Your Password") 
    st.markdown("Enter your email address and we'll send you a link to reset your password.")
    
    db = SupabaseDB()
    
    with st.form("forgot_password_form"):
        email = st.text_input(
            "Email Address", 
            placeholder="Enter your registered email"
        )
        
        submitted = st.form_submit_button("📧 Send Reset Email", use_container_width=True)
        
        if submitted:
            if not email:
                st.error("Please enter your email address.")
                return
                
            if "@" not in email or "." not in email:
                st.error("Please enter a valid email address.")
                return
            
            try:
                with st.spinner("Sending reset email..."):
                    result = db.reset_password(email)
                    
                if result.get("success"):
                    st.success("✅ " + result.get("message"))
                    st.info("💡 **Next Steps:**")
                    st.info("1. Check your email inbox (and spam folder)")
                    st.info("2. Click the reset link in the email")  
                    st.info("3. You'll be redirected here to set a new password")
                    st.info("4. Log in with your new password")
                else:
                    st.error("❌ " + result.get("error"))
                    
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    
    # Back to login link
    if st.button("⬅️ Back to Login", use_container_width=True):
        st.session_state.page = 'Login'
        if 'show_forgot_password' in st.session_state:
            del st.session_state.show_forgot_password
        st.rerun()

def show_set_new_password_form():
    """Shows the form to set a new password after recovery."""
    st.header("🔒 Set Your New Password")
    st.success("✅ Password reset verified! Please set your new password below.")
    
    # Show user info if available
    if hasattr(st.session_state, 'recovery_email'):
        st.info(f"Setting new password for: **{st.session_state.recovery_email}**")
    
    db = SupabaseDB()
    
    with st.form("set_new_password_form"):
        new_password = st.text_input(
            "New Password", 
            type="password", 
            placeholder="Enter your new password"
        )
        
        confirm_password = st.text_input(
            "Confirm New Password", 
            type="password", 
            placeholder="Confirm your new password"
        )
        
        # Password requirements
        st.markdown("**Password Requirements:**")
        st.markdown("- At least 8 characters long")
        st.markdown("- Contains at least one uppercase letter")
        st.markdown("- Contains at least one lowercase letter") 
        st.markdown("- Contains at least one number")
        
        submitted = st.form_submit_button("🔐 Set New Password", use_container_width=True, type="primary")
        
        if submitted:
            # Validation
            if not all([new_password, confirm_password]):
                st.error("Please fill in both password fields.")
                return
                
            if new_password != confirm_password:
                st.error("Passwords do not match.")
                return
                
            if len(new_password) < 8:
                st.error("Password must be at least 8 characters long.")
                return
                
            if not any(c.isupper() for c in new_password):
                st.error("Password must contain at least one uppercase letter.")
                return
                
            if not any(c.islower() for c in new_password):
                st.error("Password must contain at least one lowercase letter.")
                return
                
            if not any(c.isdigit() for c in new_password):
                st.error("Password must contain at least one number.")
                return
            
            # Attempt to set new password
            try:
                with st.spinner("Setting your new password..."):
                    result = db.set_new_password_after_recovery(new_password)
                    
                if result.get("success"):
                    st.success("🎉 " + result.get("message"))
                    st.balloons()
                    
                    # Clear recovery state and redirect to login
                    time.sleep(2)  # Give user time to see success message
                    
                    # Clean up recovery session state
                    recovery_keys = [key for key in st.session_state.keys() if 'recovery' in key]
                    for key in recovery_keys:
                        del st.session_state[key]
                    
                    st.session_state.page = 'Login'
                    st.session_state.password_reset_success = True
                    st.rerun()
                else:
                    st.error("❌ " + result.get("error"))
                    
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")

    st.divider()
    
    # Help section
    with st.expander("❓ Need Help?", expanded=False):
        st.markdown("**Having trouble?**")
        st.markdown("- Make sure your password meets all requirements above")
        st.markdown("- If this page doesn't work, the reset link may have expired")
        st.markdown("- You can request a new password reset from the login page")
        
        if st.button("🔄 Start Over - Go to Login", use_container_width=True):
            # Clean up recovery state
            recovery_keys = [key for key in st.session_state.keys() if 'recovery' in key]
            for key in recovery_keys:
                del st.session_state[key]
            st.session_state.page = 'Login'
            st.rerun()
