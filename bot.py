import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# --- CONFIGURATION ---
BOT_TOKEN = "8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I"
SPREADSHEET_ID = '1PLeziCk6pQTI9OS0K65IO8jUOBi8lNFbG2KY3olc8Qs'
RANGE_NAME = 'Sheet1!A2:A'
bot = telebot.TeleBot(BOT_TOKEN)

# --- GOOGLE SHEETS FUNCTIONS ---
def get_stock():
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        return [row[0] for row in result.get('values', []) if row]
    except Exception as e:
        print(f"Error: {e}")
        return []

def delete_stock(qty):
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=creds)
        body = {"requests": [{"deleteDimension": {"range": {"sheetId": 0, "dimension": "ROWS", "startIndex": 1, "endIndex": 1 + qty}}}]}
        service.spreadsheets().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
    except: pass

# --- RESTORED INTERFACE ---
@bot.message_handler(commands=['start'])
def start(message):
    stock = get_stock()
    if not stock:
        bot.send_message(message.chat.id, "❌ Out of Stock!\n\nWe are currently sold out of premium accounts. Please check back later or contact @ZtraxModOwner.")
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛍️ Buy Accounts", callback_data="buy"))
        bot.send_message(message.chat.id, "Welcome! Select an option:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def query(call):
    if call.data == "buy":
        stock = get_stock()
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("1 Account (₹20)", callback_data="pay_1"))
        markup.add(InlineKeyboardButton("4 Accounts (₹80)", callback_data="pay_4"))
        bot.edit_message_text(f"📈 Available Stock: {len(stock)}\n\nSelect quantity:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    
    elif call.data.startswith("pay_"):
        bot.edit_message_text("🆔 Order Ref: TXN892784\n\nScan this QR code. Once paid, click the button below to submit your UTR reference.", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    bot.infinity_polling()
