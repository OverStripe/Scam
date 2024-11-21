from telegram import Update, Bot
from telegram.ext import (
    Updater, CommandHandler, CallbackContext, MessageHandler, filters
)
import sqlite3
import os

# Replace with your bot token
BOT_TOKEN = "7832350585:AAEFJUXzDnF05Qq-U6bl-POBo7QwXeUlKh8"
OWNER_ID = 7202072688  # Your Owner ID
NOTOSCAMS_BOT_ID = 777000  # Telegram's official bot ID for system messages (@notoscam)

# Initialize SQLite database for scam reports
DB_FILE = "restricted_bot.db"

if not os.path.exists(DB_FILE):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
    CREATE TABLE reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT, -- 'user', 'group', or 'channel'
        identifier TEXT UNIQUE NOT NULL,
        reporter_id INTEGER,
        reporter_username TEXT,
        status TEXT DEFAULT 'pending' -- 'pending', 'tagged', 'not_tagged'
    )
    """)
    conn.close()


# Helper function to restrict access to the owner
def owner_only(func):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_user.id != OWNER_ID:
            update.message.reply_text("Access Denied. This bot is restricted to the owner only.")
            return
        return func(update, context, *args, **kwargs)
    return wrapper


# Start command
@owner_only
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Welcome, Owner!\n"
        "Commands:\n"
        "- /report <username> - Report a user as a scammer.\n"
        "- /report <group/channel link> - Report a group or channel.\n"
        "- /viewreports - View all reports.\n"
        "- /help - Get help."
    )


# Help command
@owner_only
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Owner Commands:\n"
        "1. /report <username> - Report a user as a scammer.\n"
        "2. /report <group/channel link> - Report a suspicious group or channel.\n"
        "3. /viewreports - View all reports."
    )


# Report command
@owner_only
def report(update: Update, context: CallbackContext) -> None:
    if context.args:
        identifier = context.args[0]
        reporter_id = update.message.from_user.id
        reporter_username = update.message.from_user.username or "Anonymous"
        conn = sqlite3.connect(DB_FILE)

        # Determine if the identifier is a user, group, or channel
        if identifier.startswith("@"):
            report_type = "user"
        elif "t.me" in identifier:
            report_type = "group" if "group" in identifier else "channel"
        else:
            update.message.reply_text("Invalid identifier. Please provide a valid username, group, or channel link.")
            return

        # Store the report locally
        try:
            conn.execute(
                "INSERT INTO reports (type, identifier, reporter_id, reporter_username) VALUES (?, ?, ?, ?)",
                (report_type, identifier, reporter_id, reporter_username)
            )
            conn.commit()

            # Notify the owner
            update.message.reply_text(f"Successfully reported {identifier} as a scammer. Sending to @notoscam...")

            # Send the report to @notoscam
            bot = Bot(BOT_TOKEN)
            try:
                bot.send_message(
                    chat_id=NOTOSCAMS_BOT_ID,
                    text=(
                        f"Report:\n"
                        f"- Type: {report_type.capitalize()}\n"
                        f"- Identifier: {identifier}\n"
                        f"- Reported by: @{reporter_username}\n\n"
                        "Please review this entity for scam tagging to prevent further fraudulent activity."
                    )
                )
                update.message.reply_text(f"Report for {identifier} has been successfully sent to @notoscam.")
            except Exception as e:
                update.message.reply_text("Failed to send the report to @notoscam. Please try again later.")
        except sqlite3.IntegrityError:
            update.message.reply_text(f"{identifier} has already been reported.")
        finally:
            conn.close()
    else:
        update.message.reply_text("Please provide a username, group, or channel to report. Example: /report @username")


# Monitor @notoscam for scam tagging
@owner_only
def monitor_notoscam(update: Update, context: CallbackContext) -> None:
    message = update.message
    bot = Bot(BOT_TOKEN)
    conn = sqlite3.connect(DB_FILE)

    if message.chat.id == NOTOSCAMS_BOT_ID:
        # Check if the message contains a scam tag notification
        if "is now marked as a scam" in message.text:
            # Extract the username or identifier
            words = message.text.split()
            identifier = [word for word in words if word.startswith("@") or "t.me" in word][0]

            # Update the database
            conn.execute(
                "UPDATE reports SET status = 'tagged' WHERE identifier = ?",
                (identifier,)
            )
            conn.commit()

            # Notify the owner
            update.message.reply_text(f"Success! {identifier} has been officially tagged as a scammer by @notoscam.")
    conn.close()


# View all reports
@owner_only
def view_reports(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect(DB_FILE)
    reports = conn.execute("SELECT type, identifier, reporter_username, status FROM reports").fetchall()
    conn.close()

    if reports:
        report_list = "\n".join(
            [f"- Type: {report_type.capitalize()}, Identifier: {identifier}, Reporter: @{reporter}, Status: {status}" 
             for report_type, identifier, reporter, status in reports]
        )
        update.message.reply_text(f"Reported Entities:\n{report_list}")
    else:
        update.message.reply_text("No reports have been made yet.")


def main():
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher

    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("report", report))
    dispatcher.add_handler(CommandHandler("viewreports", view_reports))

    # Monitor @notoscam messages
    dispatcher.add_handler(MessageHandler(Filters.chat(NOTOSCAMS_BOT_ID) & Filters.text, monitor_notoscam))

    # Start the bot
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
