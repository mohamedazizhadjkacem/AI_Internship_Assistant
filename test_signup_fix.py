#!/usr/bin/env python3
"""
Test script to verify the signup fix for duplicate key errors.
"""

from supabase_db import SupabaseDB

def test_cleanup():
    """Test the manual cleanup function."""
    try:
        db = SupabaseDB()
        print("🧹 Testing manual cleanup of orphaned records...")
        
        result = db.manual_cleanup_orphaned_records()
        if "success" in result:
            print(f"✅ Cleanup successful! Cleaned {result['cleaned']} orphaned records.")
        else:
            print(f"❌ Cleanup failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during cleanup test: {e}")

def test_signup_flow():
    """Test the improved signup flow."""
    try:
        db = SupabaseDB()
        
        # Test data - using a more realistic email format
        test_email = "testuser12345@gmail.com"
        test_password = "TestPassword123!"
        test_username = "TestUser"
        test_telegram_token = "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        test_telegram_chat = "123456789"
        
        print(f"🔧 Testing signup flow with email: {test_email}")
        
        result = db.sign_up_user(
            email=test_email,
            password=test_password,
            username=test_username,
            telegram_bot_token=test_telegram_token,
            telegram_chat_id=test_telegram_chat
        )
        
        if "success" in result:
            print("✅ Signup test successful!")
            # Clean up test user
            try:
                user_id = result.get("user", {}).id if result.get("user") else None
                if user_id:
                    print(f"🧹 Cleaning up test user: {user_id}")
                    db.client.table('profiles').delete().eq('id', user_id).execute()
                    db.client.table('subscriptions').delete().eq('id', user_id).execute()
                    db.client.auth.admin.delete_user(user_id)
                    print("✅ Test cleanup complete")
            except Exception as cleanup_e:
                print(f"⚠️ Cleanup warning: {cleanup_e}")
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"❌ Signup test failed: {error_msg}")
            
            # Check if it's the specific error we're trying to fix
            if "duplicate key value violates unique constraint" in error_msg:
                print("🔍 This is the duplicate key error we're trying to fix!")
                print("💡 Running cleanup and retrying...")
                
                # Clean orphaned records by email
                db._clean_orphaned_records_by_email(test_email)
                
                # Retry signup
                print("🔄 Retrying signup after cleanup...")
                retry_result = db.sign_up_user(
                    email=test_email,
                    password=test_password,
                    username=test_username,
                    telegram_bot_token=test_telegram_token,
                    telegram_chat_id=test_telegram_chat
                )
                
                if "success" in retry_result:
                    print("✅ Retry successful after cleanup!")
                    # Clean up the successful test user
                    try:
                        user_id = retry_result.get("user", {}).id if retry_result.get("user") else None
                        if user_id:
                            print(f"🧹 Cleaning up successful retry test user: {user_id}")
                            db.client.table('profiles').delete().eq('id', user_id).execute()
                            db.client.table('subscriptions').delete().eq('id', user_id).execute()
                            db.client.auth.admin.delete_user(user_id)
                    except Exception as cleanup_e:
                        print(f"⚠️ Retry cleanup warning: {cleanup_e}")
                else:
                    print(f"❌ Retry still failed: {retry_result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Error during signup test: {e}")

if __name__ == "__main__":
    print("🚀 Starting signup fix tests...\n")
    
    print("=" * 50)
    test_cleanup()
    
    print("\n" + "=" * 50)
    test_signup_flow()
    
    print("\n🎉 Test complete! Check the results above.")