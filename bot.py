import os
import asyncio
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)

# === CONFIGURATION ===
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_username = "songindian16@gmail.com"
email_password = "gxzk hegw vbks pavr"  # App Password (be cautious with this)
telegram_bot_token = "7506748881:AAG62PB6blgrOkUP4fegAVS89IKIhNaNzXk"
OWNER_ID = 7222795580  # Bot owner ID for privileged commands
APPROVED_USERS = {OWNER_ID}  # Approved users for using the bot

# Default Message Template
default_report_message = """
Subject: Report: User Scamming People on Telegram

Dear Telegram Support Team,

Hello, this user @{username} is a scammer, and he is scamming people under the guise of helping them. He takes money and then blocks the user.

It's a humble request to Telegram to mark this user as a scammer so that others can be warned. This action will increase trust in Telegram in the eyes of its users.

Thank you for your attention to this matter.

Sincerely,  
[Shivam Mishra]
"""

# Conversation States
USERNAME = range(1)

# Track user tasks
user_tasks = {}


# === PERMISSION CHECKS ===
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID


def is_approved(update: Update):
    return update.effective_user.id in APPROVED_USERS


# === EMAIL SENDING FUNCTION ===
async def safe_send_email(username):
    try:
        recipient_email = "abuse@telegram.org"
        message_body = default_report_message.format(username=username)

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_username, email_password)

            msg = MIMEMultipart()
            msg['From'] = email_username
            msg['To'] = recipient_email
            msg['Subject'] = "Report: User Scamming People on Telegram"
            msg.attach(MIMEText(message_body, 'plain'))

            server.sendmail(email_username, recipient_email, msg.as_string())

        return f"✅ Report sent successfully for @{username}!"
    except Exception as e:
        return f"❌ Failed to send email for @{username}: {e}"


# === COMMAND HANDLERS ===
async def start(update: Update, context):
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Welcome! Please send the **username** you want to report or type /cancel to exit."
    )
    return USERNAME


async def username_handler(update: Update, context):
    user_id = update.effective_user.id
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    username = update.message.text.strip().lstrip('@')
    await update.message.reply_text(
        f"Got the username: @{username}\nStarting auto-reporting every 2 minutes. Type /stop to cancel."
    )

    if user_id in user_tasks:
        user_tasks[user_id].cancel()

    user_tasks[user_id] = asyncio.create_task(report_task(username, context, update))
    return ConversationHandler.END


async def report_task(username, context, update):
    user_id = update.effective_user.id
    try:
        while True:
            result = await safe_send_email(username)
            await context.bot.send_message(chat_id=update.effective_chat.id, text=result)
            delay = random.randint(30, 60)  # Random delay between 30–60 seconds
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="ℹ️ Reporting task has been stopped."
        )


async def stop(update: Update, context):
    user_id = update.effective_user.id
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return ConversationHandler.END

    if user_id in user_tasks and not user_tasks[user_id].cancelled():
        user_tasks[user_id].cancel()
        del user_tasks[user_id]
        await update.message.reply_text("✅ Auto-reporting has been stopped.")
    else:
        await update.message.reply_text("ℹ️ No active reporting task to stop.")


async def cancel(update: Update, context):
    user_id = update.effective_user.id
    if user_id in user_tasks:
        user_tasks[user_id].cancel()
        del user_tasks[user_id]
    await update.message.reply_text("❌ Operation has been canceled.")
    return ConversationHandler.END


async def approve(update: Update, context):
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can approve users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Please provide a user ID. Usage: /approve <user_id>")
        return

    try:
        user_id = int(context.args[0])
        APPROVED_USERS.add(user_id)
        await update.message.reply_text(f"✅ User ID {user_id} has been approved.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")


# === MAIN FUNCTION ===
def main():
    application = ApplicationBuilder().token(telegram_bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            USERNAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, username_handler),
                CommandHandler('cancel', cancel)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler('stop', stop))
    application.add_handler(CommandHandler('approve', approve))

    application.run_polling()


# === ENTRY POINT ===
if __name__ == '__main__':
    main()
