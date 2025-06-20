from notifications import send_telegram_notification

telegram_bot_token = "bot_token"
telegram_chat_id = "YOUR_CHAT_ID_HERE"

if telegram_chat_id == "YOUR_CHAT_ID_HERE":
    print("Error: Cannot send test notification.")
    print("Please update the TELEGRAM_CHAT_ID in your config.py file first.")
else:
    print("Sending a test notification to your Telegram...")
    message = "👋 Hello! This is a test message from your AI Internship Assistant. If you received this, your notifications are working correctly!"
    send_telegram_notification(message, telegram_bot_token, telegram_chat_id)
    print("Success: Test notification script finished.")
