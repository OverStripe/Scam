from telegram import Update, Bot
from telegram.ext import Application, CommandHandler
import sqlite3
import os
import logging

# Replace with your bot token
BOT_TOKEN = "8166901002:AAHdQympBioUylhsVAA5r6SoaE3nYQ2_l64"
NOTOSCAMS_BOT_ID = 777000  # Telegram's official bot ID for system messages (@notoscam)

# Initialize logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG  # Set to DEBUG to capture all activity
)
logger = logging.getLogger(__name__)

# Initialize SQLite database for scam reports
DB_FILE = "bot_reports.db"

if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
    CREATE TABLE reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, -- 'user', 'group', or 'channel'
        identifier TEXT UNIQUE NOT NULL,
        status TEXT DEFAULT 'pending' -- 'pending', 'tagged', 'not_tagged'
    )
    """)
    conn.close()
    logger.info("Database initialized.")


# Start command
async def start(update: Update, context) -> None:
    logger.info(f"Received /start from {update.effective_user.username}")
    await update.message.reply_text(
        "Welcome to the Scam Reporter Bot!\n"
        "Commands:\n"
        "- /hello: Confirm the bot is active.\n"
        "- /report <username|group link|channel link>: Report a user, group, or channel as a scammer.\n"
        "- /status <username|link>: Check the status of a report.\n"
        "- /viewreports: View all reports.\n"
        "- /help: Get help."
    )


# Hello command
async def hello(update: Update, context) -> None:
    logger.info(f"Received /hello from {update.effective_user.username}")
    await update.message.reply_text("Hello! The bot is active and ready to assist.")


# Report command
async def report(update: Update, context) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a username, group, or channel to report. Example: /report @username")
        return

    identifier = context.args[0]
    conn = sqlite3.connect(DB_FILE)

    # Determine the type of report
    if identifier.startswith("@"):
        report_type = "user"
    elif "t.me/" in identifier:
        report_type = "group" if "group" in identifier else "channel"
    else:
        await update.message.reply_text("Invalid identifier. Please provide a valid username, group, or channel link.")
        return

    try:
        # Store the report locally
        conn.execute(
            "INSERT INTO reports (type, identifier) VALUES (?, ?)",
            (report_type, identifier)
        )
        conn.commit()

        await update.message.reply_text(f"Successfully reported {identifier} as a {report_type}. Sending to @notoscam...")
        bot = Bot(BOT_TOKEN)
        try:
            await bot.send_message(
                chat_id=NOTOSCAMS_BOT_ID,
                text=(
                    f"Hello, this {report_type} {identifier} is scamming people. "
                    f"It's a humble request to Telegram to give a scam tag to this {report_type} "
                    f"so users will know it's untrustworthy. Thank you."
                )
            )
            await update.message.reply_text(f"Report for {identifier} has been successfully sent to @notoscam.")
        except Exception as e:
            logger.error(f"Failed to send the report to @notoscam: {e}")
            await update.message.reply_text("Failed to send the report to @notoscam. Please try again later.")
    except sqlite3.IntegrityError:
        await update.message.reply_text(f"{identifier} has already been reported.")
    finally:
        conn.close()


# Check the status of a report
async def status(update: Update, context) -> None:
    if not context.args:
        await update.message.reply_text("Please provide a username or link to check the status. Example: /status @username")
        return

    identifier = context.args[0]
    conn = sqlite3.connect(DB_FILE)
    try:
        report = conn.execute(
            "SELECT type, status FROM reports WHERE identifier = ?",
            (identifier,)
        ).fetchone()

        if report:
            report_type, status = report
            await update.message.reply_text(
                f"Status of {identifier}:\n"
                f"- Type: {report_type.capitalize()}\n"
                f"- Status: {status.capitalize()}"
            )
        else:
            await update.message.reply_text(f"No report found for {identifier}.")
    finally:
        conn.close()


# View all reports
async def view_reports(update: Update, context) -> None:
    conn = sqlite3.connect(DB_FILE)
    reports = conn.execute("SELECT type, identifier, status FROM reports").fetchall()
    conn.close()

    if reports:
        report_list = "\n".join(
            [f"- Type: {report_type.capitalize()}, Identifier: {identifier}, Status: {status.capitalize()}"
             for report_type, identifier, status in reports]
        )
        await update.message.reply_text(f"Reported Entities:\n{report_list}")
    else:
        await update.message.reply_text("No reports have been made yet.")


async def main():
    logger.info("Initializing bot...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("hello", hello))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("viewreports", view_reports))

    # Start polling
    logger.info("Starting polling...")
    await application.run_polling(stop_signals=None)
    logger.info("Bot is running.")
