import logging
import os
import aiosqlite
from telegram import Update, Bot, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Application, CommandHandler, InlineQueryHandler, CallbackContext, AIORateLimiter

# Replace with your bot token and admin info
BOT_TOKEN = "7832350585:AAG9T1Vucn1I2-eOA4DTMVPW24aCOpSwSYk"
ADMIN_CHAT_ID = 7202072688  # Replace with your admin's Telegram user ID
NOTOSCAMS_BOT_ID = 777000  # Official Telegram bot for scam reports

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Database file
DB_FILE = "bot_reports.db"

# Ensure the database is initialized
async def initialize_database():
    async with aiosqlite.connect(DB_FILE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, -- 'user', 'group', or 'channel'
            identifier TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending' -- 'pending', 'tagged', 'not_tagged'
        )
        """)
        await db.commit()
        logger.info("Database initialized.")

# Command: /start
async def start(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /start from {update.effective_user.username}")
    await update.message.reply_text(
        "👋 Welcome to the Scam Reporter Bot!\n\n"
        "You can report scammers, groups, or channels and check the status of your reports.\n\n"
        "Available Commands:\n"
        "- /hello: Check if the bot is active.\n"
        "- /report <username|group link|channel link>: Report a scammer.\n"
        "- /status <username|link>: Check the status of a report.\n"
        "- /viewreports: View all reports.\n"
        "- /help: Get help.\n"
        "- Use @BotName inline for quick commands."
    )

# Command: /hello
async def hello(update: Update, context: CallbackContext) -> None:
    logger.info(f"Received /hello from {update.effective_user.username}")
    await update.message.reply_text("🤖 Hello! The bot is active and ready to assist.")

# Command: /report
async def report(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Please provide a username, group, or channel to report. Example: /report @username")
        return

    identifier = context.args[0]

    # Determine the type of report
    if identifier.startswith("@"):
        report_type = "user"
    elif "t.me/" in identifier:
        report_type = "group" if "group" in identifier else "channel"
    else:
        await update.message.reply_text("❌ Invalid identifier. Provide a valid username, group, or channel link.")
        return

    async with aiosqlite.connect(DB_FILE) as db:
        try:
            # Store the report locally
            await db.execute(
                "INSERT INTO reports (type, identifier) VALUES (?, ?)",
                (report_type, identifier)
            )
            await db.commit()

            await update.message.reply_text(f"✅ Reported {identifier} as a {report_type}. Sending to @notoscam...")

            # Send the report to @notoscam
            bot = Bot(BOT_TOKEN)
            try:
                await bot.send_message(
                    chat_id=NOTOSCAMS_BOT_ID,
                    text=(
                        f"🚨 Scam Report:\n\n"
                        f"Type: {report_type.capitalize()}\n"
                        f"Identifier: {identifier}\n\n"
                        "⚠️ Please review and take appropriate action."
                    )
                )
                await update.message.reply_text(f"✅ Report for {identifier} successfully sent to @notoscam.")
            except Exception as e:
                logger.error(f"Failed to send the report to @notoscam: {e}")
                await update.message.reply_text("❌ Failed to send the report to @notoscam. Please try again later.")

            # Notify admin
            await bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"📢 New report submitted: {identifier} ({report_type})")

        except aiosqlite.IntegrityError:
            await update.message.reply_text(f"⚠️ {identifier} has already been reported.")

# Command: /status
async def status(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("⚠️ Provide a username or link to check the status. Example: /status @username")
        return

    identifier = context.args[0]

    async with aiosqlite.connect(DB_FILE) as db:
        report = await db.execute_fetchone(
            "SELECT type, status FROM reports WHERE identifier = ?",
            (identifier,)
        )
        if report:
            report_type, status = report
            await update.message.reply_text(
                f"🔍 Status of {identifier}:\n"
                f"- Type: {report_type.capitalize()}\n"
                f"- Status: {status.capitalize()}"
            )
        else:
            await update.message.reply_text(f"❌ No report found for {identifier}.")

# Command: /viewreports
async def view_reports(update: Update, context: CallbackContext) -> None:
    async with aiosqlite.connect(DB_FILE) as db:
        reports = await db.execute_fetchall("SELECT type, identifier, status FROM reports")
        if reports:
            report_list = "\n".join(
                [f"• {report_type.capitalize()} - {identifier} ({status.capitalize()})"
                 for report_type, identifier, status in reports]
            )
            await update.message.reply_text(f"📋 Reported Entities:\n{report_list}")
        else:
            await update.message.reply_text("ℹ️ No reports have been submitted yet.")

# Command: /help
async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "💡 Help Menu:\n"
        "- /start: Start the bot.\n"
        "- /hello: Check if the bot is active.\n"
        "- /report <username|group|channel>: Report a scammer.\n"
        "- /status <username|link>: Check report status.\n"
        "- /viewreports: View all reports.\n"
        "- Use @BotName inline for quick commands."
    )

# Inline Queries
async def inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    results = [
        InlineQueryResultArticle(
            id="1",
            title="Report Scammer",
            input_message_content=InputTextMessageContent("/report @scammer_username"),
            description="Report a user, group, or channel as a scammer."
        ),
        InlineQueryResultArticle(
            id="2",
            title="View Reports",
            input_message_content=InputTextMessageContent("/viewreports"),
            description="View all submitted scam reports."
        )
    ]
    await update.inline_query.answer(results)

# Main function
async def main():
    logger.info("Starting bot...")
    await initialize_database()
    application = Application.builder().token(BOT_TOKEN).rate_limiter(AIORateLimiter()).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("viewreports", view_reports))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(InlineQueryHandler(inline_query))

    # Start polling
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
