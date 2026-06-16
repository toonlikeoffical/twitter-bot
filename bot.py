import telebot
import random
import os
import qrcode
import io
import requests  # Added to fetch stock from GitHub dynamically
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION LAYER ---
API_TOKEN = '8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I'
YOUR_UPI_ID = 'eliteascent@naviaxis'
PRICE_PER_ACCOUNT = 20

# Replace this with your exact GitHub Raw URL for stock.txt
# To get this, go to stock.txt on GitHub, click the "Raw" button, and copy the browser link.
GITHUB_STOCK_RAW_URL = "https://raw.githubusercontent.com/toonlikeoffical/twitter-bot/main/stock.txt"

bot = telebot.TeleBot(API_TOKEN, threaded=True)
user_sessions = {}

# Helper function to pull the absolute newest stock directly from GitHub
def get_live_stock():
    try:
        response = requests.get(GITHUB_STOCK_RAW_URL, timeout=10)
        if response.status_code == 200:
            # Reads and cleans lines directly from GitHub
            lines = [line.strip() for line in response.text.splitlines() if line.strip()]
            return lines
    except Exception as e:
        print(f"Error fetching live stock: {e}")
    return []

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
        lines = get_live_stock()
        count = len(lines)
        bot.answer_callback_query(call.id)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📦 Current Stock: {count} valid items available.",
            reply_markup=call.message.reply_markup
        )

    # 2. SELECT QUANTITY MENU
    elif call.data == "menu_buy":
        lines = get_live_stock()
        count = len(lines)
        bot.answer_callback_query(call.id)
        
        if count == 0:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ *Out of Stock!*\n\nWe are currently sold out of premium accounts. Please check back later or contact @ZtraxModOwner.",
                parse_mode="Markdown"
            )
            return
            
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
            text=f"🔢 *How many accounts would you like to buy?*\n\n📈 _Available Stock: {count}_\n\nSelect an option below:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 3. CHOOSE PAYMENT SYSTEM
    elif call.data.startswith("select_qty_"):
        selected_qty = int(call.data.replace("select_qty_", ""))
        lines = get_live_stock()
        current_stock = len(lines)
        
        if selected_qty > current_stock:
            bot.answer_callback_query(call.id, "⚠️ Not enough stock available!", show_alert=True)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"⚠️ *Insufficient Stock!*\n\nYou selected {selected_qty} items, but we only have *{current_stock}* left on GitHub.\n\nPlease type /start and select a package that fits our remaining stock.",
                parse_mode="Markdown"
            )
            return

        bot.answer_callback_query(call.id)
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

    # 4. GENERATE QR CODES
    elif call.data.startswith("pay_now_"):
        _, _, gateway, qty_str = call.data.split("_")
        qty = int(qty_str)
        
        lines = get_live_stock()
        current_stock = len(lines)
        if qty > current_stock:
            bot.answer_callback_query(call.id, "⚠️ Stock dropped just now!", show_alert=True)
            bot.send_message(call.message.chat.id, "❌ Sorry, inventory shifted. Payment cancelled. Please use /start to refresh.")
            return

        bot.answer_callback_query(call.id)
        total_price = qty * PRICE_PER_ACCOUNT
        transaction_id = f"TXN{random.randint(100000, 999999)}"
        
        user_sessions[transaction_id] = {"quantity": qty}

        if gateway == "upi":
            upi_url = f"upi://pay?pa={YOUR_UPI_ID}&pn=TwitterSeller&am={total_price}&cu=INR&tn={transaction_id}"
            
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(upi_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            bio = io.BytesIO()
            bio.name = 'qrcode.png'
            img.save(bio, 'PNG')
            bio.seek(0)
            
            markup = InlineKeyboardMarkup()
            btn_verify = InlineKeyboardButton("📲 Submit Reference No. (UTR)", callback_data=f"req_utr_{transaction_id}")
            markup.add(btn_verify)
            
            bot.send_photo(
                call.message.chat.id,
                bio,
                caption=f"💰 *Amount to Pay:* ₹{total_price} for {qty} accounts\n\n🆔 *Order Ref:* {transaction_id}\n\nScan this QR code. Once paid, click the button below to submit your UTR reference.",
                parse_mode="Markdown",
                reply_markup=markup,
                timeout=60
            )

        elif gateway == "crypto":
            bot.send_message(call.message.chat.id, "🌐 Crypto channels are currently offline. Please use UPI options.")

    # 5. UTR INPUT REQUEST
    elif call.data.startswith("req_utr_"):
        bot.answer_callback_query(call.id)
        tx_id = call.data.replace("req_utr_", "")
        msg = bot.send_message(call.message.chat.id, "✍️ Please enter your **12-digit UPI Reference Number / UTR**:")
        bot.register_next_step_handler(msg, process_utr_submission, tx_id)

# --- INVENTORY DELIVERY GATEWAY ---
def process_utr_submission(message, tx_id):
    utr_candidate = message.text.strip()
    
    if not utr_candidate.isdigit() or len(utr_candidate) != 12:
        bot.send_message(message.chat.id, "❌ Invalid UTR format. Must be 12 digits. Use /start to restart execution.")
        return

    if os.path.exists("used_utrs.txt"):
        with open("used_utrs.txt", "r") as f:
            used_list = f.read().splitlines()
    else:
        used_list = []

    if utr_candidate in used_list:
        bot.send_message(message.chat.id, "❌ Error: This reference has already been claimed.")
        return

    session_data = user_sessions.get(tx_id, {"quantity": 1})
    qty_to_deliver = session_data["quantity"]

    # Pull down fresh live stock right at the moment of UTR verification
    lines = get_live_stock()
    
    if len(lines) < qty_to_deliver:
        bot.send_message(message.chat.id, f"⚠️ Stock dropped! Only {len(lines)} items left. Contact support for assistance.")
        return
        
    with open("used_utrs.txt", "a") as f:
        f.write(utr_candidate + "\n")

    delivered_accounts = []
    for _ in range(qty_to_deliver):
        chosen = random.choice(lines)
        lines.remove(chosen)
        delivered_accounts.append(chosen)
    
    # Save the updated remaining stock list right back onto local memory cache safely
    if os.path.exists("stock.txt"):
        with open("stock.txt", "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n" if lines else "")
        
    accounts_text = "\n".join([f"🚀 {acc}" for acc in delivered_accounts])
    
    bot.send_message(
        message.chat.id, 
        f"🎉 *Transaction Confirmed!*\n\nHere is your purchased stock inventory item(s):\n\n📦 _Note: Remember to clear out sold items from GitHub before adding new ones._\n\n{accounts_text}",
        parse_mode="Markdown"
    )
    
    if tx_id in user_sessions:
        del user_sessions[tx_id]

print("Production Secure Shop System is live...")
bot.infinity_polling()
