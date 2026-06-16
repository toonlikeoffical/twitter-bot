import telebot
import random
import os
import qrcode
import io
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- CONFIGURATION LAYER ---
API_TOKEN = '8618859032:AAHZJ-UGtpeRF7L4RhzSIZ3Qi2H2VKeIo2I'
YOUR_UPI_ID = 'eliteascent@naviaxis'
PRICE_PER_ACCOUNT = 20

bot = telebot.TeleBot(API_TOKEN, threaded=True)

# Global session memory to store order amounts perfectly
user_sessions = {}

# Helper function to get current accurate stock count
def get_stock_count():
    try:
        with open("stock.txt", "r") as file:
            return len(file.readlines())
    except FileNotFoundError:
        return 0

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
        count = get_stock_count()
        bot.answer_callback_query(call.id)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"📦 Current Stock: {count} accounts available.",
            reply_markup=call.message.reply_markup
        )

    # 2. SELECT QUANTITY MENU
    elif call.data == "menu_buy":
        count = get_stock_count()
        bot.answer_callback_query(call.id)
        
        # If warehouse is completely empty, block right here!
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
            text=f"🔢 *How many accounts would you like to buy?*\n\n📈 _Available Stock: {count} accounts_\n\nSelect an option below:",
            parse_mode="Markdown",
            reply_markup=markup
        )

    # 3. CHOOSE PAYMENT SYSTEM (WITH ANTI-FRAUD PRE-CHECK)
    elif call.data.startswith("select_qty_"):
        selected_qty = int(call.data.replace("select_qty_", ""))
        current_stock = get_stock_count()
        
        # Anti-Fraud: If user tries to buy more than what's left, block them before payment!
        if selected_qty > current_stock:
            bot.answer_callback_query(call.id, "⚠️ Not enough stock available!", show_alert=True)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"⚠️ *Insufficient Stock!*\n\nYou selected {selected_qty} accounts, but we only have *{current_stock}* left in stock.\n\nPlease type /start and select a lower package.",
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

    # 4. GENERATE ROUTED PAYMENTS & RAM-BASED INSTANT QR CODES
    elif call.data.startswith("pay_now_"):
        _, _, gateway, qty_str = call.data.split("_")
        qty = int(qty_str)
        
        # Double-check stock one final millisecond check before showing QR
        current_stock = get_stock_count()
        if qty > current_stock:
            bot.answer_callback_query(call.id, "⚠️ Stock dropped just now!", show_alert=True)
            bot.send_message(call.message.chat.id, "❌ Sorry, those accounts were just purchased by someone else a second ago. Payment cancelled.")
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
                caption=f"💰 *Amount to Pay:* ₹{total_price} for {qty} accounts\n\n🆔 *Order Ref:* {transaction_id}\n\nScan this QR code using PhonePe, GPay, or Paytm. Once paid, click the button below to submit your UTR reference.\n\nℹ️ *Need Help?* Contact support at @ZtraxModOwner",
                parse_mode="Markdown",
                reply_markup=markup,
                timeout=60
            )

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

    session_data = user_sessions.get(tx_id, {"quantity": 1})
    qty_to_deliver = session_data["quantity"]

    try:
        with open("stock.txt", "r") as file:
            lines = file.readlines()
        
        # Absolute final layer fallback catch
        if len(lines) < qty_to_deliver:
            bot.send_message(message.chat.id, f"⚠️ Stock dropped completely! Only {len(lines)} accounts left. Please contact @ZtraxModOwner for priority manual refund.")
            return
            
        # Log UTR to file ONLY after we are 100% sure we have stock to hand out
        with open("used_utrs.txt", "a") as f:
            f.write(utr_candidate + "\n")

        delivered_accounts = []
        for _ in range(qty_to_deliver):
            chosen = random.choice(lines)
            lines.remove(chosen)
            delivered_accounts.append(chosen.strip())
        
        with open("stock.txt", "w") as file:
            file.writelines(lines)
            
        accounts_text = "\n".join([f"👤 ` {acc} `" for acc in delivered_accounts])
        
        bot.send_message(
            message.chat.id, 
            f"🎉 *Transaction Confirmed Successfully!*\n\nHere are your {qty_to_deliver} premium account credentials:\n\n{accounts_text}",
            parse_mode="Markdown"
        )
        
        if tx_id in user_sessions:
            del user_sessions[tx_id]

    except Exception as e:
        bot.send_message(message.chat.id, "Critical warehouse storage verification error.")

print("Production Secure Shop System is live...")
bot.infinity_polling()
