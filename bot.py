from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
from bs4 import BeautifulSoup
import sqlite3
import threading
import uuid
import time
import json
from collections import Counter
from textblob import TextBlob
from sklearn.feature_extraction.text import TfidfVectorizer
from googletrans import Translator
import schedule
import matplotlib.pyplot as plt

# Initialize FastAPI
app = FastAPI()

# Database setup
def setup_database():
    conn = sqlite3.connect("user_apis.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS apis (
            user_id TEXT PRIMARY KEY,
            token TEXT,
            api_data TEXT,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_user_api(user_id, token, api_data):
    conn = sqlite3.connect("user_apis.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO apis (user_id, token, api_data, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, token, api_data, int(time.time())))
    conn.commit()
    conn.close()

def get_user_api_from_db(user_id):
    conn = sqlite3.connect("user_apis.db")
    cursor = conn.cursor()
    cursor.execute("SELECT api_data FROM apis WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def generate_token():
    return str(uuid.uuid4())

# Function to scrape website data
def scrape_website(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return {"error": f"Failed to access {url}, status code: {response.status_code}"}
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract data
        headings = [item.text for item in soup.find_all(['h1', 'h2', 'h3'])]
        links = [item['href'] for item in soup.find_all('a', href=True)]
        paragraphs = [item.text for item in soup.find_all('p')]

        return {
            "url": url,
            "headings": headings,
            "links": links,
            "paragraphs": paragraphs
        }
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

# Dynamic API endpoint
@app.get("/api/{user_id}")
def get_user_api(user_id: str):
    api_data = get_user_api_from_db(user_id)
    if not api_data:
        raise HTTPException(status_code=404, detail="API not found for this user")
    return JSONResponse(content={"user_id": user_id, "api_data": eval(api_data)})

# Telegram bot logic
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Welcome! Use /gen <website_link> to generate an API from a website link.\n"
        "Available Commands:\n"
        "/help - List all commands\n"
        "/view - View your generated API\n"
        "/delete - Delete your API\n"
        "/analyze_content - Analyze content\n"
        "/extract_keywords - Extract keywords\n"
        "/translate <language_code> - Translate content\n"
        "/scrape_history - View scraping history\n"
        "/dashboard - View scraping statistics"
    )

def help_command(update: Update, context: CallbackContext):
    update.message.reply_text(
        "Available Commands:\n"
        "/start - Start the bot\n"
        "/gen <website_link> - Generate an API from a website link\n"
        "/view - View your generated API\n"
        "/delete - Delete your API\n"
        "/analyze_content - Analyze content\n"
        "/extract_keywords - Extract keywords\n"
        "/translate <language_code> - Translate content\n"
        "/scrape_history - View scraping history\n"
        "/dashboard - View scraping statistics"
    )

def generate_api(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    args = context.args

    if not args:
        update.message.reply_text("Please provide a website link. Example: /gen https://example.com")
        return

    url = args[0]

    # Scrape the website
    update.message.reply_text(f"Processing {url}, please wait...")
    scraped_data = scrape_website(url)

    if "error" in scraped_data:
        update.message.reply_text(scraped_data["error"])
    else:
        token = generate_token()
        save_user_api(user_id, token, str(scraped_data))
        api_url = f"http://127.0.0.1:8000/api/{user_id}"
        update.message.reply_text(
            f"API created successfully! Access your data here: {api_url}\n"
            f"Your API Token: {token}"
        )

def view_api(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    api_data = get_user_api_from_db(user_id)

    if not api_data:
        update.message.reply_text("No API found for your account. Use /gen to create one.")
    else:
        api_url = f"http://127.0.0.1:8000/api/{user_id}"
        update.message.reply_text(f"Your API Details:\nEndpoint: {api_url}")

def delete_api(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)

    conn = sqlite3.connect("user_apis.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM apis WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    update.message.reply_text("Your API and associated data have been deleted.")

def analyze_content(update: Update, context: CallbackContext):
    user_id = str(update.message.chat_id)
    api_data = get_user_api_from_db(user_id)

    if not api_data:
        update.message.reply_text("No API found for your account. Use /gen to create one.")
        return

    content = " ".join(eval(api_data).get("paragraphs", []))
    word_count = Counter(content.split())
    sentiment = TextBlob(content).sentiment

    update.message.reply_text(
        f"Content Analysis:\n"
        f"Top Words: {word_count.most_common(5)}\n"
        f"Sentiment: Polarity={sentiment.polarity}, Subjectivity={sentiment.subjectivity}"
    )

# More commands (extract_keywords, translate, scrape_history, dashboard, etc.) can be added here.

def main_telegram_bot():
    bot_token = "7569968947:AAG1Bx7sYHN2JLlCjOqQNA5PSRDuJJUYgHc"
    updater = Updater(bot_token, use_context=True)
    dispatcher = updater.dispatcher

    # Handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("gen", generate_api))
    dispatcher.add_handler(CommandHandler("view", view_api))
    dispatcher.add_handler(CommandHandler("delete", delete_api))
    dispatcher.add_handler(CommandHandler("analyze_content", analyze_content))

    updater.start_polling()
    updater.idle()

# Run the Telegram bot in a separate thread
if __name__ == "__main__":
    setup_database()
    threading.Thread(target=main_telegram_bot).start()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
