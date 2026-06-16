import telebot
import random
import os
import qrcode
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION LAYER ---
API_TOKEN = '8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I'
YOUR_UPI_ID = 'eliteascent@naviaxis'
PRICE_PER_ACCOUNT = 20

bot = telebot.TeleBot(API_TOKEN)

# Global session memory to store order amounts perfectly
user_sessions = {}

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
    # 1. LIVE STOCK CHECK
    if call.data == "menu_stock":
        try:
            with open("stock.txt", "r") as file:
                count = len(file.readlines())
            bot.answer_callback_query(call.id)
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"📦 Current Stock: {count} accounts available.",
                reply_markup=call.message.reply_markup
            )
        except FileNotFoundError:
            bot.send_message(call.message.chat.id, "❌ Stock database is offline.")

    # 2. SELECT QUANTITY MENU
    elif call.data == "menu_buy":
        bot.answer_callback_query(call.id)
        
        # Build beautiful instant click buttons for quantity selection
        markup = InlineKeyboardMarkup()
        btn_1 = InlineKeyboardButton("1️⃣ - Get 1 Acc (₹20)", callback_data="select_qty_1")
        btn_2 = InlineKeyboardButton("2️⃣ - Get 2 Accs (₹40)", callback_data="select_qty_2")
        btn_4 = InlineKeyboardButton("4️⃣ - Get 4 Accs (₹80)", callback_data="select_qty_4")
        btn_5 = InlineKeyboardButton("5️⃣ - Get 5 Accs (₹100)", callback_data="select_qty_5")
        
        markup.row(btn_1, btn_2)
        markup.row(btn_4, btn_5)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🔢 *How many accounts would you like to buy?*\n\nSelect a professional package option below:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 3. CHOOSE PAYMENT SYSTEM
    elif call.data.startswith("select_qty_"):
        bot.answer_callback_query(call.id)
        selected_qty = int(call.data.replace("select_qty_", ""))
        total_cost = selected_qty * PRICE_PER_ACCOUNT
        
        markup = InlineKeyboardMarkup()
        btn_upi = InlineKeyboardButton("🇮🇳 Pay via UPI", callback_data=f"pay_now_upi_{selected_qty}")
        btn_crypto = InlineKeyboardButton("🌐 Pay via Crypto", callback_data=f"pay_now_crypto_{selected_qty}")
        markup.add(btn_upi, btn_crypto)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📋 *Order Summary:*\n━━━━━━━━━━━━━━━━━━\n📦 *Quantity:* {selected_qty} accounts\n💵 *Rate:* ₹{PRICE_PER_ACCOUNT}/account\n💰 *Total Amount:* ₹{total_cost}\n━━━━━━━━━━━━━━━━━━\n\nSelect your payment gateway below:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 4. GENERATE ROUTED PAYMENTS & DYNAMIC QR CODES
    elif call.data.startswith("pay_now_"):
        bot.answer_callback_query(call.id)
        
        # Breakdown payload information securely
        _, _, gateway, qty_str = call.data.split("_")
        qty = int(qty_str)
        total_price = qty * PRICE_PER_ACCOUNT
        transaction_id = f"TXN{random.randint(100000, 999999)}"
        
        # Log quantity securely to global transaction mapping state
        user_sessions[transaction_id] = {"quantity": qty}

        if gateway == "upi":
            upi_url = f"upi://pay?pa={YOUR_UPI_ID}&pn=TwitterSeller&am={total_price}&cu=INR&tn={transaction_id}"
            
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
                    caption=f"💰 *Amount to Pay:* ₹{total_price} for {qty} accounts\n\n🆔 *Order Ref:* {transaction_id}\n\nScan this QR code using PhonePe, GPay, or Paytm. Once paid, click the button below to submit your UTR reference.\n\nℹ️ *Need Help?* Contact support at @ZtraxModOwner",
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            os.remove(qr_filename)

        elif gateway == "crypto":
            bot.send_message(
                call.message.chat.id, 
                "🌐 *Crypto Automation System*\n\nInternational merchant APIs are offline. Please use UPI options above."
            )

    # 5. INPUT REGISTRATION HANDLER FOR UTR
    elif call.data.startswith("req_utr_"):
        bot.answer_callback_query(call.id)
        tx_id = call.data.replace("req_utr_", "")
        
        msg = bot.send_message(call.message.chat.id, "✍️ Please enter or paste your **12-digit UPI Reference Number / UTR** from your banking transaction details:")
        bot.register_next_step_handler(msg, process_utr_submission, tx_id)

# --- INVENTORY DELIVERY GATEWAY ---
def process_utr_submission(message, tx_id):
    utr_candidate = message.text.strip()
    
    if not utr_candidate.isdigit() or len(utr_candidate) != 12:
        bot.send_message(message.chat.id, "❌ Invalid transaction UTR format. It must be exactly 12 numbers. Please use /start to retry.")
        return

    bot.send_message(message.chat.id, f"🔍 Validating UTR: `{utr_candidate}`...")
    
    if os.path.exists("used_utrs.txt"):
        with open("used_utrs.txt", "r") as f:
            used_list = f.read().splitlines()
    else:
        used_list = []

    if utr_candidate in used_list:
        bot.send_message(message.chat.id, "❌ Error: This reference has already been claimed or processed.")
        return

    # Fetch exact quantity recorded during checkout layer
    session_data = user_sessions.get(tx_id, {"quantity": 1})
    qty_to_deliver = session_data["quantity"]

    # Block double-claiming exploits instantly
    with open("used_utrs.txt", "a") as f:
        f.write(utr_candidate + "\n")

    # Handle bulk database item extractions
    try:
        with open("stock.txt", "r") as file:
            lines = file.readlines()
        
        if len(lines) < qty_to_deliver:
            bot.send_message(message.chat.id, f"⚠️ Stock dropped while payment went through! Only {len(lines)} accounts left. Contact @ZtraxModOwner for priority help.")
            return
            
        delivered_accounts = []
        for _ in range(qty_to_deliver):
            chosen = random.choice(lines)
            lines.remove(chosen)
            delivered_accounts.append(chosen.strip())
        
        with open("stock.txt", "w") as file:
            file.writelines(lines)
            
        # Group accounts into one beautiful output frame
        accounts_text = "\n".join([f"👤 ` {acc} `" for acc in delivered_accounts])
        
        bot.send_message(
            message.chat.id, 
            f"🎉 *Transaction Confirmed Successfully!*\n\nHere are your {qty_to_deliver} premium account credentials:\n\n{accounts_text}",
            parse_mode="Markdown"
        )
        
        # Clear out state footprint
        if tx_id in user_sessions:
            del user_sessions[tx_id]

    except Exception as e:
        bot.send_message(message.chat.id, "Critical warehouse storage verification error.")

print("Production Secure Shop System is live...")
bot.infinity_polling()
