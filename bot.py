import os
import json
import telebot
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIGURATION ---
BOT_TOKEN = "8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I"
SPREADSHEET_ID = '1S4A0SwsJ9QOn84yX2UOKisCHW9CxAnomi9vWMf3zo2E'
# This is hardcoded to your specific tab name "Accounts Sheet"
RANGE_NAME = 'Accounts Sheet!A2:A'

bot = telebot.TeleBot(BOT_TOKEN)

# --- GOOGLE SHEETS CONNECTION ---
def get_service():
    creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    creds = Credentials.from_service_info(info=creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds)

def get_stock():
    try:
        service = get_service()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        # Flattens list correctly
        return [row[0] for row in values if row]
    except Exception as e:
        print(f"DEBUG ERROR: {e}")
        return []

# --- BOT COMMANDS ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot is online.")

@bot.message_handler(commands=['stock'])
def check_stock(message):
    stock_items = get_stock()
    if not stock_items:
        bot.reply_to(message, "❌ No accounts found. Ensure the tab is named 'Accounts Sheet'.")
    else:
        bot.reply_to(message, "📈 Available:\n\n" + "\n".join(stock_items))

if __name__ == "__main__":
    bot.infinity_polling()
