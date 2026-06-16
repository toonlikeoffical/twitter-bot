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

# Memory database to track user session states (quantity and transaction mapping)
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

    elif call.data == "menu_buy":
        bot.answer_callback_query(call.id)
        
        # Step 1: Ask for quantity instead of showing payment immediately
        msg = bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="🔢 *How many accounts would you like to purchase?*\n\nPlease type a number (e.g., 1, 2, 4, 10):",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_quantity_input)

    elif call.data.startswith("pay_method_"):
        bot.answer_callback_query(call.id)
        # Parse data format: pay_method_{gateway}_{quantity}
        _, _, gateway, qty = call.data.split("_")
        qty = int(qty)
        total_price = qty * PRICE_PER_ACCOUNT
        transaction_id = f"TXN{random.randint(100000, 999999)}"
        
        # Save session data so verification knows how many accounts to release
        user_sessions[transaction_id] = {"quantity": qty, "chat_id": call.message.chat.id}

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
                    caption=f"💰 *Amount to Pay:* ₹{total_price} (for {qty} accounts)\n\n🆔 *Order Ref:* {transaction_id}\n\nScan this QR. Once paid, click the button below to submit your UTR.\n\nℹ️ *Need Help?* Contact support at @ZtraxModOwner",
                    parse_mode="Markdown",
                    reply_markup=markup
                )
            os.remove(qr_filename)

        elif gateway == "crypto":
            bot.send_message(
                call.message.chat.id, 
                "🌐 *Crypto Automation System*\n\nInternational orders require an OxaPay merchant setup. Live tracking is offline.",
                parse_mode="Markdown"
            )

    elif call.data.startswith("req_utr_"):
        bot.answer_callback_query(call.id)
        tx_id = call.data.replace("req_utr_", "")
        
        msg = bot.send_message(call.message.chat.id, "✍️ Please enter or paste your **12-digit UPI Reference Number / UTR**:")
        bot.register_next_step_handler(msg, process_utr_submission, tx_id)

# --- QUANTITY HANDLER ---
def process_quantity_input(message):
    input_text = message.text.strip()
    
    if not input_text.isdigit() or int(input_text) <= 0:
        msg = bot.send_message(message.chat.id, "❌ Invalid quantity! Please enter a valid number greater than 0. Tap /start to try again.")
        return

    requested_qty = int(input_text)

    # Check stock file to make sure you have enough to sell
    try:
        with open("stock.txt", "r") as file:
            current_stock = len(file.readlines())
    except FileNotFoundError:
        current_stock = 0

    if requested_qty > current_stock:
        bot.send_message(message.chat.id, f"❌ Out of Stock! You requested {requested_qty} accounts, but we only have {current_stock} left.\n\nTap /start to check again.")
        return

    # Dynamic Pricing calculated live
    total_cost = requested_qty * PRICE_PER_ACCOUNT

    markup = InlineKeyboardMarkup()
    btn_upi = InlineKeyboardButton("🇮🇳 Pay via UPI", callback_data=f"pay_method_upi_{requested_qty}")
    btn_crypto = InlineKeyboardButton("🌐 Pay via Crypto", callback_data=f"pay_method_crypto_{requested_qty}")
    markup.add(btn_upi, btn_crypto)

    bot.send_message(
        message.chat.id,
        f"📋 *Order Summary:*\n━━━━━━━━━━━━━━━━━━\n📦 *Quantity:* {requested_qty} accounts\n💵 *Rate:* ₹{PRICE_PER_ACCOUNT} / account\n💰 *Total Amount:* ₹{total_cost}\n━━━━━━━━━━━━━━━━━━\n\nSelect your payment gateway below:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# --- VALIDATION GATEWAY ---
def process_utr_submission(message, tx_id):
    utr_candidate = message.text.strip()
    
    if not utr_candidate.isdigit() or len(utr_candidate) != 12:
        bot.send_message(message.chat.id, "❌ Invalid transaction UTR format. It must be exactly 12 numbers.")
        return

    bot.send_message(message.chat.id, f"🔍 Checking UTR Ref: `{utr_candidate}`...")
    
    if os.path.exists("used_utrs.txt"):
        with open("used_utrs.txt", "r") as f:
            used_list = f.read().splitlines()
    else:
        used_list = []

    if utr_candidate in used_list:
        bot.send_message(message.chat.id, "❌ Error: This transaction reference number has already been processed.")
        return

    # Fetch how many accounts this transaction ID contains
    session_info = user_sessions.get(tx_id, {"quantity": 1})
    qty_to_deliver = session_info["quantity"]

    # Log UTR to anti-cheat database
    with open("used_utrs.txt", "a") as f:
        f.write(utr_candidate + "\n")

    # Release multiple items dynamically from inventory
    try:
        with open("stock.txt", "r") as file:
            lines = file.readlines()
        
        if len(lines) < qty_to_deliver:
            bot.send_message(message.chat.id, "⚠️ Stock dropped while payment was pending! Please contact administrator @ZtraxModOwner.")
            return
            
        delivered_accounts = []
        for _ in range(qty_to_deliver):
            chosen = random.choice(lines)
            lines.remove(chosen)
            delivered_accounts.append(chosen.strip())
        
        with open("stock.txt", "w") as file:
            file.writelines(lines)
            
        # Format the accounts together cleanly
        accounts_text = "\n".join([f"👤 ` {acc} `" for acc in delivered_accounts])
        
        bot.send_message(
            message.chat.id, 
            f"🎉 *Transaction Confirmed Successfully!*\n\nHere are your {qty_to_deliver} account credentials:\n\n{accounts_text}",
            parse_mode="Markdown"
        )
        
        # Clean up session memory
        if tx_id in user_sessions:
            del user_sessions[tx_id]

    except Exception as e:
        bot.send_message(message.chat.id, "Critical structural storage read error.")

print("Production Secure Shop System is live...")
bot.infinity_polling()
