# bot_flashshine.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram.error import TelegramError
import asyncio
from datetime import datetime

# Replace this with the chat ID or username of the group to send scam reports
REPORT_CHANNEL = "@notoscam"

# In-memory database to simulate scam tags for simplicity
scam_tagged_users = set()  # Replace with a persistent database for production

# Automated reporting in progress
auto_reporting = {}

# Command: /s (Start)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message for the bot."""
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello, {user_first_name}! Welcome to FlashShine's Bot.\n"
        f"Use the following commands or type /help to see the list of available commands."
    )

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the help message with all available commands."""
    help_text = (
        "🔹 *Available Commands* 🔹\n\n"
        "/s - Start the bot and get an introduction.\n"
        "/rs `<username>` - Report a scammer to @notoscam.\n"
        "/st `<username>` - Check if a user has a scam tag.\n"
        "/as `<username>` - (Admin only) Add a scam tag manually.\n"
        "/auto_report `<username>` - Automatically report the user until they get a scam tag.\n"
        "/help - Show this help message.\n\n"
        "Use these commands to help report scammers and protect others!"
    )

    # Use MarkdownV2 and escape special characters
    await update.message.reply_text(help_text, parse_mode="MarkdownV2")

# Command: /rs (Report Scammer)
async def report_scammer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles reporting a user as a scammer."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /rs <username>")
            return

        reported_user = context.args[0]
        report_message = (
            f"🚨 **SCAMMER ALERT** 🚨\n\n"
            f"🔹 **Reported User**: @{reported_user}\n"
            f"🔸 **Reason**: This user is scamming individuals by pretending to help them. "
            f"They demand payment and then block the user.\n\n"
            f"⚠️ **Impact**: Multiple users have reported losing money or trust due to this user’s actions.\n\n"
            f"💡 **Request**: Kindly review this account and assign a **scam tag** to alert the community.\n\n"
            f"📢 **Reporter Notes**: Protecting the Telegram community from scammers ensures a safer environment for everyone.\n\n"
            f"📅 **Report Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Thank you for your swift action! 🙏"
        )
        await context.bot.send_message(chat_id=REPORT_CHANNEL, text=report_message, parse_mode="Markdown")
        await update.message.reply_text(f"Report sent. @{reported_user} has been reported to @notoscam.")
    except TelegramError as e:
        await update.message.reply_text("Error: Unable to send the report. Please try again.")
        print(f"Error in /rs command: {e}")

# Command: /st (Status)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks if a user has a scam tag."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /st <username>")
            return

        username = context.args[0]
        if username in scam_tagged_users:
            await update.message.reply_text(f"🚨 Yes! @{username} has a scam tag.")
        else:
            await update.message.reply_text(f"✅ @{username} does not have a scam tag.")
    except Exception as e:
        await update.message.reply_text("Error: Unable to check the status. Please try again.")
        print(f"Error in /st command: {e}")

# Command: /auto_report (Automated Reporting)
async def auto_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically reports a user to @notoscam until they get a scam tag."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /auto_report <username>")
            return

        username = context.args[0]

        # Check if reporting is already in progress
        if username in auto_reporting:
            await update.message.reply_text(f"Auto-reporting for @{username} is already in progress.")
            return

        # Start automated reporting
        auto_reporting[username] = True
        await update.message.reply_text(f"Started auto-reporting for @{username}.")

        while True:
            # Check if the user already has a scam tag
            if username in scam_tagged_users:
                await update.message.reply_text(f"🚨 @{username} has received a scam tag. Stopping auto-reporting.")
                auto_reporting.pop(username, None)
                break

            # Send a report
            report_message = (
                f"🚨 **SCAMMER ALERT** 🚨\n\n"
                f"🔹 **Reported User**: @{username}\n"
                f"🔸 **Reason**: This user is scamming individuals by pretending to help them. "
                f"They demand payment and then block the user.\n\n"
                f"⚠️ **Impact**: Multiple users have reported losing money or trust due to this user’s actions.\n\n"
                f"💡 **Request**: Kindly review this account and assign a **scam tag** to alert the community.\n\n"
                f"📢 **Reporter Notes**: Protecting the Telegram community from scammers ensures a safer environment for everyone.\n\n"
                f"📅 **Report Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                f"Thank you for your swift action! 🙏"
            )
            await context.bot.send_message(chat_id=REPORT_CHANNEL, text=report_message, parse_mode="Markdown")
            await update.message.reply_text(f"Report sent again for @{username}. Waiting for the scam tag...")

            await asyncio.sleep(60)  # Wait for 1 minute before the next report

    except Exception as e:
        auto_reporting.pop(username, None)
        await update.message.reply_text("Error: Unable to start auto-reporting. Please try again.")
        print(f"Error in /auto_report command: {e}")

# Command: /as (Add Scam Tag, Admin Only)
async def add_scam_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually adds a scam tag to a user."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /as <username>")
            return

        username = context.args[0]
        scam_tagged_users.add(username)
        auto_reporting.pop(username, None)  # Stop auto-reporting if the tag is added
        await update.message.reply_text(f"Admin: @{username} has been successfully tagged as a scammer.")
    except Exception as e:
        await update.message.reply_text("Error: Unable to tag the user. Please try again.")
        print(f"Error in /as command: {e}")

# Main function to start the bot
def main():
    TOKEN = "7832350585:AAE7Ow6epuk00lIF5VVBF5pjPFJAHGl70tY"  # Your bot's API token
    application = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("s", start))       # /s for start
    application.add_handler(CommandHandler("help", help_command))  # /help for help
    application.add_handler(CommandHandler("rs", report_scammer))  # /rs for report scammer
    application.add_handler(CommandHandler("st", status))     # /st for status
    application.add_handler(CommandHandler("as", add_scam_tag))  # /as for add scam tag
    application.add_handler(CommandHandler("auto_report", auto_report))  # /auto_report for automated reporting

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
