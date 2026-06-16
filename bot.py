import os
import telebot
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# ========================================================
# AUTOMATIC GOOGLE SHEETS CONFIGURATION (ALREADY CONFIGURED)
# ========================================================
SPREADSHEET_ID = '1PLeziCk6pQTI9OS0K65IO8jUOBi8lNFbG2KY3olc8Qs'
RANGE_NAME = 'Sheet1!A2:A'  # Reads stock from Row 2 down

def get_google_sheets_service():
    """Authenticates using the credentials.json sitting in your folder"""
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    if not os.path.exists('credentials.json'):
        raise FileNotFoundError("ERROR: 'credentials.json' file is missing in this folder! Please check Step 5.")
    creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)
    return build('sheets', 'v4', credentials=creds)

def fetch_stock_from_sheets():
    """Fetches all available accounts from your Google Sheet"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).get('values', [])
        # Extract the account strings from rows
        return [row[0] for row in result if row]
    except Exception as e:
        print(f"[-] Error fetching data from Google Sheets: {e}")
        return []

def delete_sold_stock(num_accounts_sold):
    """Instantly deletes the sold lines from the top of your Google Sheet"""
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        
        body = {
            "requests": [
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": 0,  # Targets the first tab (Sheet1)
                            "dimension": "ROWS",
                            "startIndex": 1,  # Row 2 (0-indexed, so 1 is Row 2)
                            "endIndex": 1 + num_accounts_sold
                        }
                    }
                }
            ]
        }
        sheet.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        print(f"[+] Successfully removed {num_accounts_sold} sold account(s) from your Google Sheet!")
    except Exception as e:
        print(f"[-] Error updating Google Sheet stock rows: {e}")

# ========================================================
# EXAMPLE BOT COMMAND LOGIC INTEGRATION
# ========================================================
# NOTE: Put your actual Telegram Bot Token below
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" 
bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def check_stock_command(message):
    stock = fetch_stock_from_sheets()
    total_stock = len(stock)
    
    if total_stock == 0:
        bot.reply_to(message, "❌ Out of Stock!\n\nWe are currently sold out of premium accounts. Please check back later.")
    else:
        bot.reply_to(message, f"🔢 How many accounts would you like to buy?\n\n📈 Available Stock: {total_stock}")

# This is where the magic happens when a payment goes through successfully
def handle_successful_payment(user_id, quantity_purchased):
    stock = fetch_stock_from_sheets()
    
    if len(stock) < quantity_purchased:
        bot.send_message(user_id, "⚠️ Stock dropped while payment went through! Please contact support.")
        return

    # 1. Grab the accounts from the top of the inventory
    delivery_items = stock[:quantity_purchased]
    
    # 2. Formulate the delivery message
    delivery_message = "🎉 Transaction Confirmed Successfully!\n\nHere are your premium account credentials:\n\n"
    for item in delivery_items:
        delivery_message += f"👤 {item}\n"
        
    # 3. Deliver accounts to buyer
    bot.send_message(user_id, delivery_message)
    
    # 4. INSTANTLY delete those rows from Google Sheets so they can never be resold
    delete_sold_stock(quantity_purchased)

if __name__ == "__main__":
    print("[+] Twitter Account Seller Bot is starting up with Google Sheets integration...")
    # Uncomment the line below when your actual token is set up to test execution
    # bot.infinity_polling()
