import telebot
import random
import io
import qrcode
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIGURATION ---
BOT_TOKEN = "8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I"
SPREADSHEET_ID = '1PLeziCk6pQTI9OS0K65IO8jUOBi8lNFbG2KY3olc8Qs'
RANGE_NAME = 'Sheet1!A2:A'
PRICE = 20
bot = telebot.TeleBot(BOT_TOKEN)

# --- GOOGLE SHEETS FUNCTIONS ---
def get_service():
    creds = Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return build('sheets', 'v4', credentials=creds)

def get_stock():
    try:
        service = get_service()
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        return [row[0] for row in result.get('values', []) if row]
    except: return []

def delete_stock(qty):
    try:
        service = get_service()
        body = {"requests": [{"deleteDimension": {"range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 1, "endIndex": 1 + qty}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    except: pass

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🛍️ Buy Accounts", callback_data="buy"))
    bot.send_message(message.chat.id, "Welcome! Select an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def query(call):
    if call.data == "buy":
        stock = get_stock()
        if not stock:
            bot.answer_callback_query(call.id, "Out of stock!")
            return
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("1 Account (₹20)", callback_data="pay_1"))
        bot.send_message(call.message.chat.id, f"Stock: {len(stock)}. Select qty:", reply_markup=markup)
    
    elif call.data.startswith("pay_"):
        qty = int(call.data.split("_")[1])
        # Generate QR Logic (simplified for brevity)
        bot.send_message(call.message.chat.id, "Pay ₹20 and send UTR via /utr [number]")

@bot.message_handler(commands=['utr'])
def check_utr(message):
    # Logic to verify payment and then call delete_stock(qty)
    stock = get_stock()
    if stock:
        acc = stock[0]
        bot.send_message(message.chat.id, f"Success! Here is your account: {acc}")
        delete_stock(1)

print("Bot is fully live with Database system...")
bot.infinity_polling()
