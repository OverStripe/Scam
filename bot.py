import asyncio
import time
import re
from telethon import TelegramClient, errors
from telethon.tl.types import ChannelParticipantsAdmins
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

api_id = 28142132
api_hash = '82fe6161120bd237293a4d6da61808e3'
bot_token = '7832350585:AAECu4Nl1ec4Zu4WbAP1KYjIU7y8JyIoJIg'

client = TelegramClient('session_name', api_id, api_hash)
time_gap = 2
batch_size = 100
batch_delay = 10


def extract_group_name(group_link: str) -> str:
    match = re.match(r'(https?://)?t\.me/([^/?]+)', group_link)
    if match:
        return match.group(2)
    else:
        return group_link


async def scrape_and_invite(group_name, update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await client.start()
        print("Client started. Fetching participants...")

        participants = await client.get_participants(group_name)
        print(f"Fetched {len(participants)} members from {group_name}.")

        if not participants:
            await context.bot.send_message(chat_id=update.effective_chat.id, text="No participants found. Ensure the account has access to the group.")
            return

        admins = await client.get_participants(group_name, filter=ChannelParticipantsAdmins)
        admin_ids = {admin.id for admin in admins}
        print(f"Found {len(admins)} admins.")

        members = [
            {"id": user.id, "username": user.username, "first_name": user.first_name, "last_name": user.last_name}
            for user in participants if user.id not in admin_ids
        ]

        print(f"Members excluding admins: {len(members)}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Found {len(members)} members (excluding admins).")

        total_batches = (len(members) + batch_size - 1) // batch_size
        for batch_index in range(total_batches):
            start_index = batch_index * batch_size
            end_index = start_index + batch_size
            batch = members[start_index:end_index]
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Processing Batch {batch_index + 1}/{total_batches}...")
            await send_invites(batch, update, context)
            if batch_index < total_batches - 1:
                await asyncio.sleep(batch_delay)
    except Exception as e:
        print(f"Error during scraping: {e}")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")
    finally:
        await client.disconnect()


async def send_invites(members, update: Update, context: ContextTypes.DEFAULT_TYPE):
    successful_invites = []
    failed_invites = []
    for member in members:
        try:
            message = f"Hi {member['first_name']}, join us at our group!"
            await client.send_message(member['id'], message)
            successful_invites.append(member)
            print(f"Sent invite to {member['id']} - {member['username']}")
        except Exception as e:
            failed_invites.append(member)
            print(f"Failed to send invite to {member['id']}: {e}")
        time.sleep(time_gap)

    print(f"Invites sent: {len(successful_invites)}")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Sent invites to {len(successful_invites)} members.")


async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /scrape <group_link_or_username>")
        return

    group_name = extract_group_name(context.args[0])
    await scrape_and_invite(group_name, update, context)


def main():
    application = Application.builder().token(bot_token).build()
    application.add_handler(CommandHandler("scrape", scrape))
    application.run_polling()


if __name__ == "__main__":
    main()
