"""
Test script for Telegram Bot functionality
Run this script to test if your bot token and chat ID are working correctly
"""

from notifications import send_telegram_notification

def test_telegram_bot():
    """Test your Telegram bot configuration"""
    
    print("🤖 Telegram Bot Test Script")
    print("=" * 50)
    
    # Get bot credentials from user
    bot_token = input("Enter your Bot Token: ").strip()
    chat_id = input("Enter your Chat ID: ").strip()
    
    if not bot_token or not chat_id:
        print("❌ Error: Please provide both Bot Token and Chat ID")
        return
    
    print(f"\n📡 Testing bot with:")
    print(f"Token ending in: ...{bot_token[-10:]}")
    print(f"Chat ID: {chat_id}")
    print("\n🔄 Sending test message...")
    
    # Test message
    test_message = """
🎉 <b>Bot Test Successful!</b>

✅ Your Telegram bot is working correctly!

<b>Bot Details:</b>
• Token: Configured ✓
• Chat ID: Configured ✓
• Connection: Active ✓

<i>You can now use this bot with the AI Internship Assistant for notifications.</i>
    """.strip()
    
    try:
        # Send the test notification
        send_telegram_notification(test_message, bot_token, chat_id)
        print("✅ Test message sent successfully!")
        print("📱 Check your Telegram to see the message.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if your Bot Token is correct")
        print("2. Verify your Chat ID is correct")
        print("3. Make sure you've started a chat with your bot")
        print("4. Ensure your bot token hasn't expired")

def test_with_simple_message():
    """Test with a simple message"""
    
    print("\n" + "="*50)
    print("🔄 Testing with simple message...")
    
    bot_token = input("Enter your Bot Token: ").strip()
    chat_id = input("Enter your Chat ID: ").strip()
    
    simple_message = "Hello! This is a simple test message. 🤖"
    
    try:
        send_telegram_notification(simple_message, bot_token, chat_id)
        print("✅ Simple test successful!")
    except Exception as e:
        print(f"❌ Simple test failed: {str(e)}")

def validate_credentials():
    """Validate the format of bot credentials"""
    
    print("\n" + "="*50)
    print("🔍 Credential Validation")
    
    bot_token = input("Enter your Bot Token to validate: ").strip()
    chat_id = input("Enter your Chat ID to validate: ").strip()
    
    # Validate bot token format
    if ':' in bot_token and len(bot_token.split(':')) == 2:
        bot_id, token_part = bot_token.split(':', 1)
        if bot_id.isdigit() and len(token_part) >= 35:
            print("✅ Bot Token format looks correct")
        else:
            print("❌ Bot Token format appears invalid")
    else:
        print("❌ Bot Token format appears invalid")
        print("   Expected format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
    
    # Validate chat ID format
    if chat_id.lstrip('-').isdigit():
        print("✅ Chat ID format looks correct")
    else:
        print("❌ Chat ID format appears invalid")
        print("   Expected format: 123456789 or -123456789")

if __name__ == "__main__":
    print("🤖 Telegram Bot Testing Tool")
    print("=" * 50)
    
    while True:
        print("\nChoose an option:")
        print("1. 🧪 Full Bot Test (Recommended)")
        print("2. 📝 Simple Message Test")
        print("3. 🔍 Validate Credentials Format")
        print("4. ❌ Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            test_telegram_bot()
        elif choice == "2":
            test_with_simple_message()
        elif choice == "3":
            validate_credentials()
        elif choice == "4":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")