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

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcome message for the bot."""
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello, {user_first_name}! Welcome to FlashShine's Anti-Scam Bot.\n\n"
        f"I am here to help identify scammers and protect the Telegram community. Use the /help command to see available actions."
    )

# Command: /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays the help message with all available commands."""
    help_text = (
        "📋 *List of Commands*\n\n"
        "1. /start - Start the bot and get an introduction.\n"
        "2. /rs `<username>` - Report a scammer to @notoscam.\n"
        "3. /st `<username>` - Check if a user has a scam tag.\n"
        "4. /as `<username>` - (Admin only) Add a scam tag manually.\n"
        "5. /auto_report `<username>` - Automatically report a user every 5 minutes until they receive a scam tag.\n"
        "6. /mass_reporting `<user1> <user2> ...` - Report multiple scammers simultaneously.\n"
        "7. /spread `<username>` - Notify others to report a scammer collaboratively.\n"
        "8. /help - Show this help message.\n\n"
        "⚠️ Note: The /auto_report feature will ensure scam reports continue until the user receives a scam tag."
    )

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
            f"**Scam Report Request**\n\n"
            f"**Reported User**: @{reported_user}\n\n"
            f"This individual has been reported for scamming users by pretending to help them. "
            f"They request payment and subsequently block users after receiving money.\n\n"
            f"Kindly review this account and assign a *scam tag* to warn others and maintain a safe community environment.\n\n"
            f"Your prompt action on this matter will help enhance trust in Telegram. Thank you for your efforts.\n\n"
            f"**Report Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await context.bot.send_message(chat_id=REPORT_CHANNEL, text=report_message, parse_mode="MarkdownV2")
        await update.message.reply_text(f"The user @{reported_user} has been reported to @notoscam for further review.")
    except TelegramError as e:
        await update.message.reply_text("Error: Unable to send the report. Please try again.")
        print(f"Error in /rs command: {e}")

# Command: /auto_report (Automated Reporting)
async def auto_report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically reports a user to @notoscam every 5 minutes until they get a scam tag."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /auto_report <username>")
            return

        username = context.args[0]

        # Check if reporting is already in progress
        if username in auto_reporting:
            await update.message.reply_text(f"Automated reporting for @{username} is already in progress.")
            return

        # Start automated reporting
        auto_reporting[username] = True
        await update.message.reply_text(f"Automated reporting for @{username} has started. Reports will continue every 5 minutes until the user receives a scam tag.")

        while auto_reporting[username]:
            if username in scam_tagged_users:
                await update.message.reply_text(f"The user @{username} has been assigned a scam tag. Automated reporting has stopped.")
                auto_reporting.pop(username, None)
                break

            # Send the report message
            report_message = (
                f"**Scam Report Request**\n\n"
                f"**Reported User**: @{username}\n\n"
                f"This individual has been reported for scamming users by pretending to help them. "
                f"They request payment and subsequently block users after receiving money.\n\n"
                f"Kindly review this account and assign a *scam tag* to warn others and maintain a safe community environment.\n\n"
                f"Your prompt action on this matter will help enhance trust in Telegram. Thank you for your efforts.\n\n"
                f"**Report Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await context.bot.send_message(chat_id=REPORT_CHANNEL, text=report_message, parse_mode="MarkdownV2")
            await update.message.reply_text(f"Another report for @{username} has been submitted. Reports will continue every 5 minutes until a scam tag is assigned.")
            await asyncio.sleep(300)  # Wait 5 minutes (300 seconds) before sending the next report
    except Exception as e:
        auto_reporting.pop(username, None)
        await update.message.reply_text("Error: Unable to start automated reporting. Please try again.")
        print(f"Error in /auto_report command: {e}")

# Command: /spread (Encourage Collaborative Reporting)
async def spread_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Encourage users to report a scammer collaboratively."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /spread <username>")
            return

        username = context.args[0]
        spread_message = (
            f"Attention: A scammer @{username} has been identified.\n\n"
            f"We need your help to report this user to Telegram. Please use the /rs <username> command or manually flag their account to ensure they receive a scam tag.\n\n"
            f"Collaborative efforts will help protect the community and prevent further scams. Thank you for your support!"
        )
        await update.message.reply_text(spread_message)
    except Exception as e:
        await update.message.reply_text("Error: Unable to share the message. Please try again.")
        print(f"Error in /spread command: {e}")

# Command: /mass_reporting (Report Multiple Scammers)
async def mass_reporting(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports multiple users as scammers."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /mass_reporting <username1> <username2> ...")
            return

        reported_users = context.args
        for user in reported_users:
            report_message = (
                f"**Scam Report Request**\n\n"
                f"**Reported User**: @{user}\n\n"
                f"This individual has been reported for scamming users by pretending to help them. "
                f"They request payment and subsequently block users after receiving money.\n\n"
                f"Kindly review this account and assign a *scam tag* to warn others and maintain a safe community environment.\n\n"
                f"Your prompt action on this matter will help enhance trust in Telegram. Thank you for your efforts.\n\n"
                f"**Report Timestamp**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            await context.bot.send_message(chat_id=REPORT_CHANNEL, text=report_message, parse_mode="MarkdownV2")
            await asyncio.sleep(2)  # Delay to avoid spamming

        await update.message.reply_text(f"Mass reporting completed for users: {', '.join(reported_users)}.")
    except TelegramError as e:
        await update.message.reply_text("Error: Unable to complete mass reporting. Please try again.")
        print(f"Error in /mass_reporting command: {e}")

# Command: /st (Check Scam Tag Status)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Checks if a user has a scam tag."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /st <username>")
            return

        username = context.args[0]
        if username in scam_tagged_users:
            await update.message.reply_text(f"The user @{username} currently has a scam tag.")
        else:
            await update.message.reply_text(f"The user @{username} does not have a scam tag yet.")
    except Exception as e:
        await update.message.reply_text("Error: Unable to check the status. Please try again.")
        print(f"Error in /st command: {e}")

# Command: /as (Admin-Only: Add Scam Tag)
async def add_scam_tag(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually adds a scam tag to a user."""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /as <username>")
            return

        username = context.args[0]
        scam_tagged_users.add(username)
        auto_reporting.pop(username, None)  # Stop auto-reporting if the tag is added
        await update.message.reply_text(f"The user @{username} has been manually assigned a scam tag by an admin.")
    except Exception as e:
        await update.message.reply_text("Error: Unable to assign a scam tag. Please try again.")
        print(f"Error in /as command: {e}")

# Main function to start the bot
def main():
    TOKEN = "7832350585:AAEkP_YPu9-ycbyP4fMm0M9quh5fLbICZd4"  # Replace with your actual bot token
    application = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rs", report_scammer))
    application.add_handler(CommandHandler("auto_report", auto_report))
    application.add_handler(CommandHandler("spread", spread_message))
    application.add_handler(CommandHandler("mass_reporting", mass_reporting))
    application.add_handler(CommandHandler("st", status))
    application.add_handler(CommandHandler("as", add_scam_tag))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
