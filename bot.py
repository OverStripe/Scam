# bot_flashshine.py

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message when the bot is started."""
    user_first_name = update.effective_user.first_name
    await update.message.reply_text(
        f"Hello, {user_first_name}! Welcome to FlashShine's Bot. 🎉\n"
        "I'm here to assist you. Type anything, and I'll echo it back!"
    )

# Echo function
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Replies with the same message."""
    await update.message.reply_text(update.message.text)

# Main function to start the bot
def main():
    TOKEN = "7832350585:AAG9T1Vucn1I2-eOA4DTMVPW24aCOpSwSYk"  # Replace with your bot's API token
    application = ApplicationBuilder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start))

    # Message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Start the bot
    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
