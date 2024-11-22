from telethon import TelegramClient, errors
from telethon.tl.types import ChannelParticipantsAdmins
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import time
import re

# Your Telegram API credentials
api_id = 28142132
api_hash = '82fe6161120bd237293a4d6da61808e3'
bot_token = '8166901002:AAGIb0YmsjIUHNtx_prQNgkdynq_cj0dEtM'

client = TelegramClient('session_name', api_id, api_hash)
time_gap = 2  # Time gap (in seconds) between each message
batch_delay = 10  # Delay (in seconds) between batches
batch_size = 100  # Number of members to process per batch
target_group_invite_link = "https://t.me/clash_of_clans_accounts_Group"  # Replace with your target group invite link


def extract_group_name(group_link: str) -> str:
    """
    Extract the group username or ID from the provided group link.
    """
    match = re.match(r'(https?://)?t\.me/([^/?]+)', group_link)
    if match:
        return match.group(2)
    else:
        return group_link  # If it's not a link, assume it's a username or ID


async def scrape_and_invite(group_name, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Scrape members from a group, exclude admins, and send invites automatically in batches.
    """
    try:
        await client.start()

        # Fetch all participants
        participants = await client.get_participants(group_name)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Fetched {len(participants)} members from {group_name}.")

        # Fetch all admins
        admins = await client.get_participants(group_name, filter=ChannelParticipantsAdmins)
        admin_ids = {admin.id for admin in admins}
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Identified {len(admins)} admins. They will be excluded from invites.")

        # Exclude admins from participants
        members = []
        for user in participants:
            if user.id not in admin_ids:  # Exclude admins
                user_id = user.id
                username = user.username or "No Username"
                first_name = user.first_name or "No First Name"
                last_name = user.last_name or "No Last Name"
                members.append({"id": user_id, "username": username, "first_name": first_name, "last_name": last_name})

        # Automatically send invites in batches
        total_batches = (len(members) + batch_size - 1) // batch_size
        for batch_index in range(total_batches):
            start_index = batch_index * batch_size
            end_index = start_index + batch_size
            batch = members[start_index:end_index]
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Processing Batch {batch_index + 1}/{total_batches}...")
            await send_invites(batch, target_group_invite_link, update, context)
            if batch_index < total_batches - 1:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Waiting {batch_delay} seconds before the next batch...")
                await asyncio.sleep(batch_delay)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")
    finally:
        await client.disconnect()


async def send_invites(members, invite_link, update: Update, context: ContextTypes.DEFAULT_TYPE, retry_attempts=3):
    """
    Send invite links to a batch of members.
    """
    successful_invites = []
    failed_invites = []
    total_members = len(members)

    for index, member in enumerate(members):
        for attempt in range(1, retry_attempts + 1):
            try:
                # Send personalized invite
                message = (
                    f"Hi {member['first_name']},\n\n"
                    f"Join our exclusive group for exciting updates!\n\n"
                    f"Click here: {invite_link}"
                )
                await client.send_message(member['id'], message)
                successful_invites.append(member)
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"({index+1}/{total_members}) Invite sent to {member['first_name']} ({member['username']}).")

                # Add time gap
                time.sleep(time_gap)
                break  # Exit the retry loop on success
            except errors.FloodWaitError as e:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Rate limit hit. Waiting for {e.seconds} seconds. Retry attempt {attempt}/{retry_attempts}.")
                await asyncio.sleep(e.seconds)
            except errors.UserPrivacyRestrictedError:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Cannot send message to {member['first_name']} ({member['username']}): Privacy restriction.")
                failed_invites.append({"id": member['id'], "username": member['username'], "reason": "Privacy Restriction"})
                break  # Skip retries for privacy issues
            except Exception as e:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Failed to send message to {member['first_name']} ({member['username']}): {e}. Retry attempt {attempt}/{retry_attempts}.")
                if attempt == retry_attempts:  # Log only after final retry attempt
                    failed_invites.append({"id": member['id'], "username": member['username'], "reason": str(e)})

    # Generate summary for the batch
    summary = (
        f"Batch Summary:\n"
        f"Total Members Processed: {total_members}\n"
        f"Successfully Invited: {len(successful_invites)}\n"
        f"Failed Invites: {len(failed_invites)}\n"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=summary)


async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Trigger scraping and invite sending in batches using a group link.
    """
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /scrape <group_link_or_username>")
        return

    group_input = context.args[0]
    group_name = extract_group_name(group_input)  # Extract username or ID from the link
    await scrape_and_invite(group_name, update, context)


def main():
    """
    Main function to run the bot with infinite polling.
    """
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("scrape", scrape))

    application.run_polling(allowed_updates=Update.ALL_TYPES, close_loop=False)


if __name__ == "__main__":
    main()
