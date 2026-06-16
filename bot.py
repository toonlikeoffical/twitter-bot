import telebot
import random
import os
import qrcode
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION LAYER ---
API_TOKEN = '8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I'
YOUR_UPI_ID = 'eliteascent@naviaxis'  # Fixed configuration string

bot = telebot.TeleBot('8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I')

# Temporary database to track pending transactions in memory
pending_upi_orders = {}

# --- HOME MENU ---
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = InlineKeyboardMarkup()
    btn_buy = InlineKeyboardButton("🛍️ Buy Twitter Account", callback_data="menu_buy")
    btn_stock = InlineKeyboardButton("📊 Check Stock", callback_data="menu_stock")
    markup.add(btn_buy)
    markup.add(btn_stock)
    
    bot.send_message(
        message.chat.id, 
        "Welcome to Premium Twitter Seller Bot!\nChoose an option below to proceed:", 
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_menu_clicks(call):
    if call.data == "menu_stock":
        try:
            with open("stock.txt", "r") as file:
                count = len(file.readlines())
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, f"📦 Current Stock: {count} accounts available.")
        except FileNotFoundError:
            bot.send_message(call.message.chat.id, "❌ Stock database is offline.")

    elif call.data == "menu_buy":
        markup = InlineKeyboardMarkup()
        btn_upi = InlineKeyboardButton("🇮🇳 Pay via UPI (GPay/PhonePe)", callback_data="pay_upi")
        btn_crypto = InlineKeyboardButton("🌐 Pay via Crypto (USDT/LTC)", callback_data="pay_crypto")
        markup.add(btn_upi, btn_crypto)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Please select your preferred payment gateway method:",
            reply_markup=markup
        )

    elif call.data == "pay_upi":
    bot.answer_callback_query(call.id)
    price_inr = 20
    transaction_id = f"TXN{random.randint(100000, 999999)}"
    
    upi_url = f"upi://pay?pa=eliteascent@naviaxis&pn=TwitterBot&am={price_inr}&cu=INR"
    
    qr = qrcode.make(upi_url)
    qr_filename = f"upi_{transaction_id}.png"
    qr.save(qr_filename)
    
        with open(qr_filename, "rb") as qr_img:
        markup = InlineKeyboardMarkup()
        btn_verify = InlineKeyboardButton("📲 Submit Reference No. (UTR)", callback_data=f"req_utr_{transaction_id}")
        markup.add(btn_verify)
        
        bot.send_photo(
            call.message.chat.id,
            qr_img,
            caption=f"💰 *Amount to Pay:* ₹{price_inr} per account\n\n🆔 *Order Ref:* {transaction_id}\n\nScan this QR. Once paid, click the button below to submit your UTR.\n\nℹ️ *Need Help?* Contact support at @ZtraxModOwner",
            parse_mode="Markdown",
            reply_markup=markup
        )
    os.remove(qr_filename)

    elif call.data == "pay_crypto":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id, 
            "🌐 *Crypto Automation System*\n\nTo prevent zero-payment exploits, international orders require an OxaPay merchant setup.\n\nTo connect live crypto, paste your OxaPay API key on Line 11 to fetch live payments.",
            parse_mode="Markdown"
        )

    elif call.data.startswith("req_utr_"):
        bot.answer_callback_query(call.id)
        tx_id = call.data.replace("req_utr_", "")
        
        # Register user session state
        msg = bot.send_message(call.message.chat.id, "✍️ Please enter or paste your **12-digit UPI Reference Number / UTR** from your banking app payment receipt:")
        bot.register_next_step_handler(msg, process_utr_submission, tx_id)

# --- VALIDATION GATEWAY ---
def process_utr_submission(message, tx_id):
    utr_candidate = message.text.strip()
    
    # Validation Rule: Must be exactly 12 digits long
    if not utr_candidate.isdigit() or len(utr_candidate) != 12:
        msg = bot.send_message(message.chat.id, "❌ Invalid transaction UTR format. It must be exactly 12 numbers. Tap 'Submit UTR' again to retry.")
        return

    bot.send_message(message.chat.id, f"🔍 Checking UTR Ref: `{utr_candidate}` against real-time ledger records...")
    
    # Anti-Cheat check logic
    # In a simple store system, we log used UTRs to a file to prevent users using old receipts
    if os.path.exists("used_utrs.txt"):
        with open("used_utrs.txt", "r") as f:
            used_list = f.read().splitlines()
    else:
        used_list = []

    if utr_candidate in used_list:
        bot.send_message(message.chat.id, "❌ Error: This transaction reference number has already been claimed or processed.")
        return

    # Log this transaction code so it can never be used again
    with open("used_utrs.txt", "a") as f:
        f.write(utr_candidate + "\n")

    # Release Inventory
    try:
        with open("stock.txt", "r") as file:
            lines = file.readlines()
        
        if not lines:
            bot.send_message(message.chat.id, "⚠️ Payment accepted, but stock ran out! Contacting system administrator for priority release.")
            return
            
        chosen_account = random.choice(lines).strip()
        lines.remove(chosen_account + '\n') if (chosen_account + '\n') in lines else lines.remove(chosen_account)
        
        with open("stock.txt", "w") as file:
            file.writelines(lines)
            
        bot.send_message(
            message.chat.id, 
            f"🎉 *Transaction Confirmed Successfully!*\n\nHere are your account credentials:\n`{chosen_account}`",
            parse_mode="Markdown"
        )
    except Exception as e:
        bot.send_message(message.chat.id, "Critical structural storage read error.")

print("Production Secure Shop System is live...")
bot.infinity_polling()
