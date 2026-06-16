import os
import json
import telebot
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIGURATION ---
# These are your specific credentials
BOT_TOKEN = "8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I"
SPREADSHEET_ID = '1S4A0SwsJ9QOn84yX2UOKisCHW9CxAnomi9vWMf3zo2E'
# This points exactly to your 'Accounts Sheet' tab, rows A2 and below
RANGE_NAME = 'Accounts Sheet!A2:A'

bot = telebot.TeleBot(BOT_TOKEN)

# --- GOOGLE SHEETS CONNECTION ---
def get_service():
    # Reads the JSON key from the 'GOOGLE_CREDENTIALS' environment variable in Render
    creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    creds = Credentials.from_service_info(info=creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds)

def get_stock():
    try:
        service = get_service()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        # Flattens the data into a readable list
        return [item[0] for item in values if item]
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return []

# --- BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot is online! Use /stock to see available accounts.")

@bot.message_handler(commands=['stock'])
def check_stock(message):
    stock_items = get_stock()
    if not stock_items:
        bot.reply_to(message, "❌ No accounts found in 'Accounts Sheet' or connection error.")
    else:
        # Formats the list nicely for Telegram
        response = "📈 Available Accounts:\n\n" + "\n".join(stock_items)
        bot.reply_to(message, response)

if __name__ == "__main__":
    print("Bot is starting...")
    bot.infinity_polling()
