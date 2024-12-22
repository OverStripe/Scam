import os
import asyncio
import smtplib
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, filters

# Configuration (Use dedicated email credentials)
smtp_server = "smtp.gmail.com"
smtp_port = 587
email_username = "songindian16@gmail.com"
email_password = "gxzk hegw vbks pavr"
telegram_bot_token = "7506748881:AAG9qqUApTyEsSXYV7jL5vQbawbr13cdthY"
OWNER_ID = 7222795580
APPROVED_USERS = {OWNER_ID}

# Email Template
default_report_message = """
Subject: Report: User Scamming People on Telegram

Dear Telegram Support Team,

Hello, this user @{username} is a scammer, and he is scamming people under the guise of helping them. He takes money and then blocks the user.

It's a humble request to Telegram to mark this user as a scammer so that others can be warned. This action will increase trust in Telegram in the eyes of its users.

Thank you for your attention to this matter.

Sincerely,  
[Shivam Mishra]
"""

# Global task tracker
user_tasks = {}

# Permission checks
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

def is_approved(update: Update):
    return update.effective_user.id in APPROVED_USERS

# Safe email sender with delay
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

# Bulk reporting with throttling
async def bulk_report_handler(update: Update, context):
    if not is_approved(update):
        await update.message.reply_text("❌ You are not authorized to use this bot.")
        return

    usernames = context.args
    if len(usernames) == 0:
        await update.message.reply_text("❌ Please provide at least one username. Usage: /bulk_report @user1 @user2 ...")
        return

    await update.message.reply_text(f"📨 Starting bulk report for {len(usernames)} users. Please wait...")

    for username in usernames:
        username = username.strip().lstrip('@')
        result = await safe_send_email(username)
        await update.message.reply_text(result)
        
        # Add random delay between 30–60 seconds to avoid rate limits
        delay = random.randint(30, 60)
        await asyncio.sleep(delay)

    await update.message.reply_text("✅ Bulk report process completed successfully!")

# Cancel operation
async def cancel(update: Update, context):
    user_id = update.effective_user.id
    if user_id in user_tasks:
        user_tasks[user_id].cancel()
        del user_tasks[user_id]
    await update.message.reply_text("❌ Operation has been canceled.")
    return ConversationHandler.END

# Approve users
async def approve(update: Update, context):
    if not is_owner(update):
        await update.message.reply_text("❌ Only the owner can approve users.")
        return

    if len(context.args) != 1:
        await update.message.reply_text("Please provide a user ID to approve. Usage: /approve <user_id>")
        return

    try:
        user_id = int(context.args[0])
        APPROVED_USERS.add(user_id)
        await update.message.reply_text(f"✅ User ID {user_id} has been approved.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Please provide a valid number.")

# Main function
def main():
    application = ApplicationBuilder().token(telegram_bot_token).build()

    application.add_handler(CommandHandler('bulk_report', bulk_report_handler))
    application.add_handler(CommandHandler('approve', approve))
    application.add_handler(CommandHandler('cancel', cancel))

    application.run_polling()

# Entry point
if __name__ == '__main__':
    main()
  
