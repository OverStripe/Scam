from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio
import time
from telethon import TelegramClient, errors
from telethon.tl.types import ChannelParticipantsAdmins

# Your Telegram API credentials
api_id = 28142132
api_hash = '82fe6161120bd237293a4d6da61808e3'
bot_token = '8166901002:AAEQpQN9fuJbe9YEjTDURS43790f-RabMFc'

client = TelegramClient('session_name', api_id, api_hash)
time_gap = 2  # Time gap (in seconds) between each message
target_group_invite_link = "https://t.me/clash_of_clans_accounts_Group"  # Replace with your target group invite link


async def scrape_and_invite(group_name, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Scrape members from a group, exclude admins, and send invites automatically.
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
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Members (excluding admins) successfully saved to 'group_members.csv'.")

        # Automatically send invites
        await send_invites(members, target_group_invite_link, update, context)

    except Exception as e:
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Error: {e}")
    finally:
        await client.disconnect()


async def send_invites(members, invite_link, update: Update, context: ContextTypes.DEFAULT_TYPE, retry_attempts=3):
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
    await context.bot.send_message(chat_id=update.effective_chat.id, text=summary)


async def scrape(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Trigger scraping and invite sending.
    """
    if len(context.args) < 1:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Usage: /scrape <group_name>")
        return

    group_name = context.args[0]
    await scrape_and_invite(group_name, update, context)


def main():
    """
    Main function to run the bot.
    """
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("scrape", scrape))

    application.run_polling()


if __name__ == "__main__":
    main()
