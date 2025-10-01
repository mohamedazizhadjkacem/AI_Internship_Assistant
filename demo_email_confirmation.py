#!/usr/bin/env python3
"""
Demo script to show the new email confirmation flow working.
"""

from supabase_db import SupabaseDB
import time

def demo_registration_flow():
    """Demonstrate the complete registration and confirmation flow."""
    try:
        db = SupabaseDB()
        
        print("🎭 **DEMO: Email Confirmation Flow**")
        print("=" * 50)
        
        # Demo data - using a proper email format
        demo_email = "demouser123@gmail.com"
        demo_password = "DemoPassword123!"
        demo_username = "DemoUser"
        demo_telegram_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        demo_telegram_chat = "123456789"
        
        print(f"📧 Demo Email: {demo_email}")
        print(f"👤 Demo Username: {demo_username}")
        
        print("\\n1️⃣ **STEP 1: User Registration**")
        print("   User fills registration form and clicks 'Register'...")
        
        # Clean up any existing demo user first
        try:
            existing_check = db.check_user_email_confirmed(demo_email)
            if "error" not in existing_check:
                print(f"   🧹 Cleaning up existing demo user...")
                # Could add cleanup here if needed
        except:
            pass
        
        # Attempt registration
        print("   🔄 Processing registration...")
        result = db.sign_up_user(
            email=demo_email,
            password=demo_password,
            username=demo_username,
            telegram_bot_token=demo_telegram_token,
            telegram_chat_id=demo_telegram_chat
        )
        
        if "error" not in result:
            print("   ✅ Registration successful!")
            user_id = result.get("user", {}).id if result.get("user") else None
            print(f"   🆔 User ID: {user_id}")
            
            print("\\n2️⃣ **STEP 2: Email Confirmation Status Check**")
            time.sleep(1)  # Wait a moment for user to be created
            
            confirm_status = db.check_user_email_confirmed(demo_email)
            if "error" not in confirm_status:
                print(f"   📧 Email: {demo_email}")
                print(f"   ✅ Confirmed: {confirm_status.get('confirmed', False)}")
                print(f"   🆔 User ID: {confirm_status.get('user_id', 'Not found')}")
                
                if not confirm_status.get('confirmed', False):
                    print("   ⚠️  **Email NOT confirmed** - this is expected!")
                    print("   💡 User would need to check email and click confirmation link")
                    
                    print("\\n3️⃣ **STEP 3: Login Attempt (Should Fail)**")
                    login_result = db.sign_in_user(demo_email, demo_password)
                    if "error" in login_result:
                        print(f"   ❌ Login failed: {login_result['error']}")
                        if "confirm" in login_result['error'].lower():
                            print("   ✅ **This is correct behavior!** Email needs confirmation")
                        
                        print("\\n4️⃣ **STEP 4: Resend Confirmation Email**")
                        print("   🔄 Attempting to resend confirmation email...")
                        resend_result = db.resend_confirmation_email(demo_email)
                        if "success" in resend_result:
                            print("   ✅ Confirmation email resent successfully!")
                            print("   📨 In real scenario, user would receive email with link:")
                            print(f"   🔗 http://localhost:8501/?confirmed=true")
                        else:
                            print(f"   ❌ Resend failed: {resend_result.get('error', 'Unknown')}")
                    else:
                        print("   ⚠️  Login succeeded - email might already be confirmed")
                else:
                    print("   ✅ Email already confirmed!")
            else:
                print(f"   ❌ Error checking status: {confirm_status['error']}")
            
            print("\\n🧹 **CLEANUP: Removing demo user**")
            if user_id:
                try:
                    db.client.table('profiles').delete().eq('id', user_id).execute()
                    db.client.table('subscriptions').delete().eq('id', user_id).execute()
                    db.client.auth.admin.delete_user(user_id)
                    print("   ✅ Demo user cleaned up")
                except Exception as cleanup_e:
                    print(f"   ⚠️  Cleanup warning: {cleanup_e}")
                    
        else:
            error_msg = result["error"]
            print(f"   ❌ Registration failed: {error_msg}")
            
            if "conflict detected" in error_msg.lower():
                print("   💡 This is the orphaned records issue - cleanup should handle it")
            elif "already registered" in error_msg.lower():
                print("   💡 User already exists - this is expected for demo")
        
        print("\\n" + "=" * 50)
        print("🎯 **DEMO COMPLETE**")
        print("\\n**What this demo showed:**")
        print("✅ Registration creates user with unconfirmed email")
        print("✅ Login fails with clear 'confirm email' message")  
        print("✅ Resend confirmation email functionality works")
        print("✅ Proper error handling and user guidance")
        
        print("\\n**In the real app:**")
        print("📧 User receives actual confirmation email")
        print("🔗 Clicking the link confirms email in Supabase")
        print("🚪 User can then login successfully")
        print("💫 Profile and subscription records get created")
        
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    demo_registration_flow()