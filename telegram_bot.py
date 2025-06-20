import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from supabase_db import get_supabase_client, get_or_create_user_by_telegram_id, add_internship, get_internships_by_user, delete_internship, update_internship_status
from scraper import scrape_linkedin

# Import config
try:
    from config import TELEGRAM_BOT_TOKEN
except ImportError:
    print("Error: TELEGRAM_BOT_TOKEN not found in config.py")
    exit()

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Conversation States ---
GET_TITLE, GET_COMPANY, GET_LINK, GET_DESCRIPTION, GET_SOURCE_URL, GET_SOURCE_SITE = range(6)
GET_SCRAPE_QUERY, GET_SCRAPE_LOCATION = range(7, 9)

# --- Constants for Internship Statuses ---
STATUS_OPTIONS = ["Applied", "Interviewing", "Offer", "Rejected", "Saved"]

# --- Bot Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    logger.info(f"/start by {user.username}")
    supabase = get_supabase_client()
    if not supabase:
        await update.message.reply_text("DB connection failed.")
        return

    profile, is_new = get_or_create_user_by_telegram_id(supabase, {'id': user.id, 'username': user.username})
    context.user_data['profile'] = profile

    if profile:
        reply = f"Welcome back, {user.mention_html()}!"
        if is_new:
            reply = f"Welcome, {user.mention_html()}! Your account is set up."
        reply += "\n\nUse /add to save an internship or /view to see your list."
        await update.message.reply_html(reply)
    else:
        await update.message.reply_text("Sorry, could not set up your account.")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new internship."""
    user = update.effective_user
    supabase = get_supabase_client()
    profile, _ = get_or_create_user_by_telegram_id(supabase, {'id': user.id, 'username': user.username})
    if not profile:
        await update.message.reply_text("Could not find your profile. Please try /start again.")
        return ConversationHandler.END
    context.user_data['profile'] = profile
    
    await update.message.reply_text("Let's add a new internship. What is the job title?")
    return GET_TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['job_title'] = update.message.text
    await update.message.reply_text("Got it. Now, what is the company name?")
    return GET_COMPANY

async def get_company(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['company_name'] = update.message.text
    await update.message.reply_text("Great. What is the application link or email?")
    return GET_LINK

async def get_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['application_link'] = update.message.text
    await update.message.reply_text("Thanks. Now, please provide a brief job description. (Or /skip)")
    return GET_DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['job_description'] = update.message.text
    await update.message.reply_text("Perfect. What is the source URL? (e.g., the original job post link) (Or /skip)")
    return GET_SOURCE_URL

async def get_source_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['source_url'] = update.message.text
    await update.message.reply_text("Almost done. What is the source site? (e.g., LinkedIn, Indeed) (Or /skip)")
    return GET_SOURCE_SITE

async def _save_internship(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Helper function to save internship data to the database."""
    supabase = get_supabase_client()
    profile = context.user_data.get('profile')

    job_data = {
        'job_title': context.user_data.get('job_title'),
        'company_name': context.user_data.get('company_name'),
        'application_link': context.user_data.get('application_link'),
        'job_description': context.user_data.get('job_description'),
        'source_url': context.user_data.get('source_url'),
        'source_site': context.user_data.get('source_site'),
    }

    result = add_internship(supabase, profile['id'], job_data)

    if result and 'error' in result:
        await update.message.reply_text(f"Error: {result['message']}")
    elif result:
        await update.message.reply_text("Success! I've saved this internship.")
    else:
        await update.message.reply_text("An unexpected error occurred.")

    context.user_data.clear()

async def get_source_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the source site and saves the internship."""
    context.user_data['source_site'] = update.message.text
    await _save_internship(update, context)
    return ConversationHandler.END

async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the job description field."""
    context.user_data['job_description'] = None
    await update.message.reply_text("Skipped. What is the source URL? (Or /skip)")
    return GET_SOURCE_URL

async def skip_source_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the source URL field."""
    context.user_data['source_url'] = None
    await update.message.reply_text("Skipped. What is the source site? (Or /skip)")
    return GET_SOURCE_SITE

async def skip_source_site(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the source site field and saves the internship."""
    context.user_data['source_site'] = None
    await _save_internship(update, context)
    return ConversationHandler.END

# --- Scraper Command Handlers ---

async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to scrape for new internships."""
    await update.message.reply_text("Let's find some internships for you. What job title are you looking for? (e.g., 'Software Engineer Intern')")
    return GET_SCRAPE_QUERY

async def get_scrape_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the job title and asks for the location."""
    context.user_data['scrape_query'] = update.message.text
    await update.message.reply_text("Great. Now, what location should I search in? (e.g., 'United States')")
    return GET_SCRAPE_LOCATION

async def get_scrape_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores location, runs scraper, saves results, and notifies user."""
    location = update.message.text
    query = context.user_data['scrape_query']
    user = update.effective_user
    
    await update.message.reply_text(f"Scraping for '{query}' in '{location}'. This might take a moment...")

    supabase = get_supabase_client()
    profile = context.user_data.get('profile')
    if not profile:
        profile, _ = get_or_create_user_by_telegram_id(supabase, {'id': user.id, 'username': user.username})
        if not profile:
            await update.message.reply_text("I couldn't find your profile to save the jobs. Please try /start first.")
            return ConversationHandler.END
    
    scraped_jobs = scrape_linkedin(job_title=query, location=location)
    
    if not scraped_jobs:
        await update.message.reply_text("I couldn't find any new internships with that query. Try a different search.")
        return ConversationHandler.END
        
    new_count = 0
    duplicate_count = 0
    error_count = 0
    
    for job in scraped_jobs:
        result = add_internship(supabase, profile['id'], job)
        if result and 'error' in result and result['error'] == 'duplicate':
            duplicate_count += 1
        elif result:
            new_count += 1
        else:
            error_count += 1
            
    message = f"Scraping complete! ✨\n\n"
    message += f"✅ Found and saved {new_count} new internships.\n"
    if duplicate_count > 0:
        message += f"👍 Found {duplicate_count} internships that were already in your list.\n"
    if error_count > 0:
        message += f"❌ Encountered {error_count} errors while saving.\n"
        
    message += "\nYou can see them all with the /view command."
    
    await update.message.reply_text(message)
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Operation cancelled.")
    context.user_data.clear()
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles inline button presses for updating and deleting internships."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    # Callback data is in the format "action_internshipId_optionalData"
    parts = query.data.split('_')
    action = parts[0]
    internship_id = int(parts[1])

    user_id = context.user_data.get('user_id')
    supabase = get_supabase_client()

    # Ensure user_id is available, fetching if necessary
    if not user_id:
        telegram_user = query.from_user
        user_id, _ = get_or_create_user_by_telegram_id(supabase, telegram_user.id, telegram_user.username)
        if user_id:
            context.user_data['user_id'] = user_id
        else:
            await query.edit_message_text(text="Error: Could not identify your profile. Please /start again.")
            return

    # --- Handle DELETE action ---
    if action == 'delete':
        success = delete_internship(supabase, user_id, internship_id)
        if success:
            await query.edit_message_text(text="🗑️ Internship has been deleted.")
        else:
            await query.edit_message_text(text="Error: Could not delete internship.")

    # --- Handle UPDATE action (show status options) ---
    elif action == 'update':
        status_buttons = [
            InlineKeyboardButton(status, callback_data=f"setstatus_{internship_id}_{status}")
            for status in STATUS_OPTIONS
        ]
        # Group buttons into rows of 2 for a cleaner look
        keyboard = [status_buttons[i:i + 2] for i in range(0, len(status_buttons), 2)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_reply_markup(reply_markup=reply_markup)

    # --- Handle SETSTATUS action (apply the new status) ---
    elif action == 'setstatus':
        new_status = parts[2]
        updated_job = update_internship_status(supabase, user_id, internship_id, new_status)

        if updated_job:
            # Re-create the original keyboard with Delete and Update buttons
            original_keyboard = [
                [
                    InlineKeyboardButton("✏️ Update Status", callback_data=f"update_{updated_job['id']}"),
                    InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{updated_job['id']}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(original_keyboard)

            # Re-create the message content with the new status
            message_text = (
                f"<b>{updated_job['job_title']} at {updated_job['company_name']}</b>\n"
                f"- <b>Status:</b> {updated_job.get('status', 'N/A')}\n"
                f"- <b>Description:</b> {updated_job.get('job_description', 'N/A')}\n"
                f"- <b>Source:</b> <a href='{updated_job.get('source_url', '#')}'>{updated_job.get('source_site', 'N/A')}</a>\n"
                f"- <b>Apply:</b> <a href='{updated_job.get('application_link', '#')}'>Link</a>"
            )
            await query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup,
                parse_mode='HTML',
                disable_web_page_preview=True
            )
        else:
            await query.edit_message_text(text="Error: Could not update status.")

async def view_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays all saved internships for the user."""
    user = update.effective_user
    logger.info(f"/view by {user.username}")
    supabase = get_supabase_client()

    profile = context.user_data.get('profile')
    if not profile:
        profile, _ = get_or_create_user_by_telegram_id(supabase, {'id': user.id, 'username': user.username})
        if not profile:
            await update.message.reply_text("Could not find your profile. Please try /start.")
            return
        context.user_data['profile'] = profile

    internships = get_internships_by_user(supabase, profile['id'])

    if not internships:
        await update.message.reply_text("You haven't saved any internships yet. Use /add.")
        return

    await update.message.reply_text("Here are your saved internships:")
    for job in internships:
        keyboard = [
            [
                InlineKeyboardButton("✏️ Update Status", callback_data=f"update_{job['id']}"),
                InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{job['id']}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        message = (
            f"<b>{job['job_title']} at {job['company_name']}</b>\n"
            f"- <b>Status:</b> {job.get('status', 'N/A')}\n"
            f"- <b>Description:</b> {job.get('job_description', 'N/A')}\n"
            f"- <b>Source:</b> <a href='{job.get('source_url', '#')}'>{job.get('source_site', 'N/A')}</a>\n"
            f"- <b>Apply:</b> <a href='{job.get('application_link', '#')}'>Link</a>"
        )
        await update.message.reply_html(message, reply_markup=reply_markup, disable_web_page_preview=True)

def main() -> None:
    """Sets up and runs the bot."""
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for adding internships
    add_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add_command)],
        states={
            GET_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            GET_COMPANY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_company)],
            GET_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            GET_DESCRIPTION: [
                CommandHandler('skip', skip_description),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)
            ],
            GET_SOURCE_URL: [
                CommandHandler('skip', skip_source_url),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_source_url)
            ],
            GET_SOURCE_SITE: [
                CommandHandler('skip', skip_source_site),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_source_site)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
        per_chat=True,
    )

    # Conversation handler for scraping
    scrape_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('scrape', scrape_command)],
        states={
            GET_SCRAPE_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_scrape_query)],
            GET_SCRAPE_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_scrape_location)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        per_user=True,
        per_chat=True,
    )

    # Add all handlers to the application
    application.add_handler(add_conv_handler)
    application.add_handler(scrape_conv_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("view", view_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot is starting...")
    application.run_polling()



if __name__ == "__main__":
    main()
