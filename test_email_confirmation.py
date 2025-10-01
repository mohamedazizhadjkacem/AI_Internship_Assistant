#!/usr/bin/env python3
"""
Test script to verify email confirmation functionality.
"""

from supabase_db import SupabaseDB

def test_email_confirmation():
    """Test email confirmation checking functionality."""
    try:
        db = SupabaseDB()
        
        # Test with a known email (replace with actual test email)
        test_email = "testuser12345@gmail.com"
        
        print(f"🔍 Checking email confirmation status for: {test_email}")
        
        # Check confirmation status
        result = db.check_user_email_confirmed(test_email)
        
        if "error" in result:
            print(f"❌ Error checking confirmation: {result['error']}")
        else:
            print(f"📧 Email: {test_email}")
            print(f"✅ Confirmed: {result.get('confirmed', False)}")
            print(f"🆔 User ID: {result.get('user_id', 'Not found')}")
            print(f"📅 Confirmation sent: {result.get('confirmation_sent_at', 'Not available')}")
            
            if not result.get('confirmed', False):
                print(f"\n💡 User exists but email not confirmed - this explains login issues!")
                
                print(f"\n🔧 Testing resend confirmation email...")
                resend_result = db.resend_confirmation_email(test_email)
                
                if "success" in resend_result:
                    print("✅ Confirmation email resent successfully!")
                else:
                    print(f"❌ Failed to resend: {resend_result.get('error', 'Unknown error')}")
            else:
                print(f"\n✅ Email is confirmed - user should be able to log in!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_login_with_unconfirmed():
    """Test login attempt with unconfirmed email."""
    try:
        db = SupabaseDB()
        
        test_email = "testuser12345@gmail.com"
        test_password = "TestPassword123!"
        
        print(f"\\n🔐 Testing login with potentially unconfirmed email: {test_email}")
        
        result = db.sign_in_user(test_email, test_password)
        
        if "error" in result:
            print(f"❌ Login failed: {result['error']}")
            if "confirm your email" in result['error'].lower():
                print("💡 This confirms the issue - email needs to be confirmed!")
        else:
            print("✅ Login successful!")
            
    except Exception as e:
        print(f"❌ Error during login test: {e}")

if __name__ == "__main__":
    print("🚀 Testing email confirmation functionality...\\n")
    
    print("=" * 60)
    test_email_confirmation()
    
    print("\\n" + "=" * 60)
    test_login_with_unconfirmed()
    
    print(f"\\n🎯 **Summary:**")
    print(f"- If user exists but not confirmed: Registration worked, but email needs confirmation")
    print(f"- If login fails with 'confirm email': This is the exact issue")
    print(f"- Solution: User must click email confirmation link or use resend feature")
    print(f"\\n📧 **Email Confirmation Process:**")
    print(f"1. User registers → Gets confirmation email")
    print(f"2. User clicks link in email → Email gets confirmed in Supabase")
    print(f"3. User returns to app → Can now login successfully")
    print(f"\\n🔧 **If confirmation link doesn't work:**")
    print(f"- Check Supabase email templates")
    print(f"- Verify redirect URL is correct")
    print(f"- Use 'Resend Confirmation' button in app")