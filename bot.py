from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters
import sqlite3
import os

# Replace with your bot token
BOT_TOKEN = "7832350585:AAG-BlrTwF5Sjpg_mrujQAi5nFDasO6eT0w"
AUTHORIZED_USERNAME = "@FlashShine"  # Authorized username
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
        status TEXT DEFAULT 'pending' -- 'pending', 'tagged', 'not_tagged'
    )
    """)
    conn.close()


# Helper function to restrict access to @FlashShine
def authorized_user_only(func):
    def wrapper(update: Update, context: CallbackContext, *args, **kwargs):
        if update.effective_user.username != AUTHORIZED_USERNAME.lstrip("@"):
            update.message.reply_text("Access Denied. This bot can only be used by @FlashShine.")
            return
        return func(update, context, *args, **kwargs)
    return wrapper


# Start command
@authorized_user_only
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        f"Welcome, {AUTHORIZED_USERNAME}!\n"
        "Commands:\n"
        "- /report <username> - Report a user as a scammer.\n"
        "- /status <username> - Check the status of a report.\n"
        "- /viewreports - View all reports.\n"
        "- /help - Get help."
    )


# Help command
@authorized_user_only
def help_command(update: Update, context: CallbackContext) -> None:
    update.message.reply_text(
        "Commands:\n"
        "1. /report <username> - Report a user as a scammer.\n"
        "2. /status <username> - Check the status of a report.\n"
        "3. /viewreports - View all reports."
    )


# Report command
@authorized_user_only
def report(update: Update, context: CallbackContext) -> None:
    if context.args:
        username = context.args[0]
        conn = sqlite3.connect(DB_FILE)

        # Store the report locally
        try:
            conn.execute(
                "INSERT INTO reports (type, identifier) VALUES (?, ?)",
                ("user", username)
            )
            conn.commit()

            # Notify the user
            update.message.reply_text(f"Successfully reported {username} as a scammer. Sending to @notoscam...")

            # Send the report to @notoscam
            bot = Bot(BOT_TOKEN)
            try:
                bot.send_message(
                    chat_id=NOTOSCAMS_BOT_ID,
                    text=(
                        f"Hello, this user {username} is a scammer and he is scamming people by the name of helping them. "
                        f"He takes money and then blocks the user. It's a humble request to Telegam that please give a scam tag "
                        f"to this user so that users will come to know that he is a scammer. This will increase the trust of "
                        f"Telegram in the eyes of its users. Thanks."
                    )
                )
                update.message.reply_text(f"Report for {username} has been successfully sent to @notoscam.")
            except Exception as e:
                update.message.reply_text("Failed to send the report to @notoscam. Please try again later.")
        except sqlite3.IntegrityError:
            update.message.reply_text(f"{username} has already been reported.")
        finally:
            conn.close()
    else:
        update.message.reply_text("Please provide a username to report. Example: /report @username")


# Check the status of a report
@authorized_user_only
def status(update: Update, context: CallbackContext) -> None:
    if context.args:
        username = context.args[0]
        conn = sqlite3.connect(DB_FILE)
        try:
            report = conn.execute(
                "SELECT type, status FROM reports WHERE identifier = ?",
                (username,)
            ).fetchone()

            if report:
                report_type, status = report
                update.message.reply_text(
                    f"Status of {username}:\n"
                    f"- Type: {report_type.capitalize()}\n"
                    f"- Status: {status.capitalize()}"
                )
            else:
                update.message.reply_text(f"No report found for {username}.")
        finally:
            conn.close()
    else:
        update.message.reply_text("Please provide a username to check the status. Example: /status @username")


# View all reports
@authorized_user_only
def view_reports(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect(DB_FILE)
    reports = conn.execute("SELECT identifier, status FROM reports").fetchall()
    conn.close()

    if reports:
        report_list = "\n".join(
            [f"- {identifier}: {status.capitalize()}" for identifier, status in reports]
        )
        update.message.reply_text(f"Reported Users:\n{report_list}")
    else:
        update.message.reply_text("No reports have been made yet.")


def main():
    # Create the Application with your bot token
    application = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("report", report))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("viewreports", view_reports))

    # Run the bot with infinite polling
    application.run_polling(stop_signals=None)


if __name__ == "__main__":
    main()
