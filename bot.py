from telethon import TelegramClient, errors
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsAdmins, ChannelParticipantsSearch
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import asyncio
import time

# Your Telegram API credentials
api_id = 28142132  # Replace with your Telegram API ID
api_hash = '82fe6161120bd237293a4d6da61808e3'  # Replace with your Telegram API Hash
bot_token = '8166901002:AAEQpQN9fuJbe9YEjTDURS43790f-RabMFc'  # Replace with your Telegram bot token

client = TelegramClient('session_name', api_id, api_hash)
time_gap = 2  # Time gap (in seconds) between each message
target_group_invite_link = "https://t.me/clash_of_clans_accounts_Group"  # Replace with your target group invite link


async def scrape_and_invite(group_name, update: Update):
    """
    Scrape members from a group, exclude admins, and send invites automatically.
    """
    try:
        await client.start()

        # Fetch all participants
        participants = await client.get_participants(group_name)
        update.message.reply_text(f"Fetched {len(participants)} members from {group_name}.")

        # Fetch all admins
        admins = await client.get_participants(group_name, filter=ChannelParticipantsAdmins)
        admin_ids = {admin.id for admin in admins}
        update.message.reply_text(f"Identified {len(admins)} admins. They will be excluded from invites.")

        # Exclude admins from participants
        members = []
        with open("group_members.csv", "w") as file:
            file.write("user_id,username,first_name,last_name\n")
            for user in participants:
                if user.id not in admin_ids:  # Exclude admins
                    user_id = user.id
                    username = user.username or "No Username"
                    first_name = user.first_name or "No First Name"
                    last_name = user.last_name or "No Last Name"
                    members.append({"id": user_id, "username": username, "first_name": first_name, "last_name": last_name})
                    file.write(f"{user_id},{username},{first_name},{last_name}\n")
        update.message.reply_text(f"Members (excluding admins) successfully saved to 'group_members.csv'.")

        # Automatically send invites
        await send_invites(members, target_group_invite_link, update)

    except Exception as e:
        update.message.reply_text(f"Error: {e}")
    finally:
        await client.disconnect()


async def send_invites(members, invite_link, update: Update, retry_attempts=3):
    """
    Send invite links to all scraped members.
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
                update.message.reply_text(f"({index+1}/{total_members}) Invite sent to {member['first_name']} ({member['username']}).")

                # Add time gap
                time.sleep(time_gap)
                break  # Exit the retry loop on success
            except errors.FloodWaitError as e:
                update.message.reply_text(f"Rate limit hit. Waiting for {e.seconds} seconds. Retry attempt {attempt}/{retry_attempts}.")
                await asyncio.sleep(e.seconds)
            except errors.UserPrivacyRestrictedError:
                update.message.reply_text(f"Cannot send message to {member['first_name']} ({member['username']}): Privacy restriction.")
                failed_invites.append({"id": member['id'], "username": member['username'], "reason": "Privacy Restriction"})
                break  # Skip retries for privacy issues
            except Exception as e:
                update.message.reply_text(f"Failed to send message to {member['first_name']} ({member['username']}): {e}. Retry attempt {attempt}/{retry_attempts}.")
                if attempt == retry_attempts:  # Log only after final retry attempt
                    failed_invites.append({"id": member['id'], "username": member['username'], "reason": str(e)})

    # Log results
    with open("successful_invites.log", "w") as success_file:
        for member in successful_invites:
            success_file.write(f"{member['id']},{member['username']}\n")
    with open("failed_invites.log", "w") as fail_file:
        for member in failed_invites:
            fail_file.write(f"{member['id']},{member['username']},{member['reason']}\n")

    # Generate summary report
    summary = (
        f"Invitation Summary:\n"
        f"Total Members Processed: {total_members}\n"
        f"Successfully Invited: {len(successful_invites)}\n"
        f"Failed Invites: {len(failed_invites)}\n"
    )
    update.message.reply_text(summary)


def start(update: Update, context: CallbackContext):
    """
    Start command for the bot.
    """
    update.message.reply_text(
        "Welcome to the Telegram Scraper Bot!\n\n"
        "Commands:\n"
        "/scrape <group_name> - Scrape members (excluding admins) and send invites automatically"
    )


def scrape(update: Update, context: CallbackContext):
    """
    Trigger scraping and invite sending.
    """
    if len(context.args) < 1:
        update.message.reply_text("Usage: /scrape <group_name>")
        return

    group_name = context.args[0]

    async def process_scrape_and_invite():
        await scrape_and_invite(group_name, update)

    asyncio.run(process_scrape_and_invite())


def main():
    """
    Main function to run the bot.
    """
    updater = Updater(token=bot_token, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("scrape", scrape))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
