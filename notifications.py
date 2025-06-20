import telegram
import asyncio

def send_telegram_notification(message, telegram_bot_token, telegram_chat_id):
    if not all([telegram_bot_token, telegram_chat_id]):
        print("Error: Telegram credentials not configured.")
        return

    try:
        bot = telegram.Bot(token=telegram_bot_token)
        # Always use asyncio for python-telegram-bot v20+
        asyncio.run(bot.send_message(chat_id=telegram_chat_id, text=message, parse_mode='HTML'))
        print(f"Successfully sent notification to chat ID ending in ...{str(telegram_chat_id)[-4:]}")
    except Exception as e:
        print(f"Error sending Telegram notification: {e}")