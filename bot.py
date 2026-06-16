import os
import json
import telebot
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

BOT_TOKEN = "8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I"
SPREADSHEET_ID = '1S4A0SwsJ9QOn84yX2UOKisCHW9CxAnomi9vWMf3zo2E'
# Targeted precisely at the tab name in your screenshot
RANGE_NAME = 'Accounts Sheet!A2:A'

bot = telebot.TeleBot(BOT_TOKEN)

def get_service():
    creds_dict = json.loads(os.environ['GOOGLE_CREDENTIALS'])
    creds = Credentials.from_service_info(info=creds_dict, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds)

def get_stock():
    try:
        service = get_service()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get('values', [])
        # This will return the actual list found
        return [row[0] for row in values if row]
    except Exception as e:
        # This will print the actual reason in the Render Logs
        print(f"FAILED TO FETCH: {e}")
        return None

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Bot is online.")

@bot.message_handler(commands=['stock'])
def check_stock(message):
    stock = get_stock()
    if stock is None:
        bot.reply_to(message, "Error: Could not connect to sheet. Check logs.")
    elif not stock:
        bot.reply_to(message, "The sheet 'Accounts Sheet' is empty.")
    else:
        bot.reply_to(message, "📈 Available Accounts:\n" + "\n".join(stock))

if __name__ == "__main__":
    bot.infinity_polling()
