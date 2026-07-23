import os
import random
import string
import requests
from flask import Flask, request, jsonify
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_IDS = [7172828025, 8705494010]
PRIMARY_ADMIN_ID = 7172828025

# Razorpay Keys
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'rzp_test_TGrOAdSNybrtLb')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', '4RDT6rNXxygnnSG0WK5F7OTR')

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- PRODUCTS CONFIG ---
PRODUCTS = {
    "main_id": {
        "name": "🛒 MAIN ID PANEL",
        "prices": {"1d": 100, "3d": 250, "7d": 450, "15d": 800, "30d": 1200}
    },
    "prime": {
        "name": "💧 PRIME HOOK",
        "prices": {"1d": 60, "3d": 140, "7d": 250, "15d": 400, "30d": 600}
    },
    "drip": {
        "name": "🔺 DRIP CLIENT",
        "prices": {"1d": 60, "3d": 140, "7d": 250, "15d": 400, "30d": 600}
    }
}

DAYS_MAP = {
    "1d": "1 Day",
    "3d": "3 Days",
    "7d": "7 Days",
    "15d": "15 Days",
    "30d": "30 Days"
}

stock_keys = {
    f"{p}:{d}": [] 
    for p in PRODUCTS.keys() 
    for d in ["1d", "3d", "7d", "15d", "30d"]
}

pending_orders = {}
user_orders = {}
user_states = {}

def is_admin(user_id):
    return user_id in ADMIN_IDS

def safe_delete(chat_id, message_id):
    try:
        bot.delete_message(chat_id, message_id)
    except Exception:
        pass

# --- RAZORPAY PAYMENT LINK GENERATOR ---
def create_razorpay_payment_link(amount, description, customer_name, order_id):
    url = "https://api.razorpay.com/v1/payment_links"
    payload = {
        "amount": amount * 100,  # Razorpay accepts in paise
        "currency": "INR",
        "accept_partial": False,
        "description": description,
        "customer": {
            "name": customer_name
        },
        "notify": {
            "sms": False,
            "email": False
        },
        "reminder_enable": False,
        "notes": {
            "order_id": order_id
        },
        "callback_url": "https://t.me/",
        "callback_method": "get"
    }
    
    try:
        response = requests.post(
            url, 
            json=payload, 
            auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
        )
        data = response.json()
        if "short_url" in data:
            return data["short_url"]
        return None
    except Exception as e:
        print("Razorpay Error:", e)
        return None

# --- TEXT MESSAGES ---
WELCOME_TEXT = (
    "👋 Welcome, Hassan X\n\n"
    "★ — 👑 Hassan X Mod Store 👑 — ★\n\n"
    "🔑 Premium All Best Mod Keys\n"
    "⚡ Instant Auto Delivery 24/7\n"
    "🔒 100% Secure Payment (Razorpay)\n"
    "🏷 Best Prices Guaranteed\n"
    "🎁 High Discount Rewards\n"
    "🎧 Active Support For Set-Up\n\n"
    "🚀 Tap Shop Now To Start!"
)

# --- INLINE MENUS ---
def get_start_inline_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("🛒 Shop Now", callback_data="nav:open_shop"))
    markup.add(
        types.InlineKeyboardButton("🔑 My Orders", callback_data="user:purchases"),
        types.InlineKeyboardButton("👤 Profile", callback_data="user:profile")
    )
    markup.add(
        types.InlineKeyboardButton("❓ How to Use", callback_data="info:how_to_buy"),
        types.InlineKeyboardButton("🎧 Support", callback_data="user:support")
    )
    return markup

def get_main_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 MAIN ID PANEL", callback_data="select:main_id"),
        types.InlineKeyboardButton("💧 PRIME HOOK", callback_data="select:prime"),
        types.InlineKeyboardButton("🔺 DRIP CLIENT", callback_data="select:drip"),
        types.InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:go_start")
    )
    return markup

def get_category_inline(panel_key):
    markup = types.InlineKeyboardMarkup(row_width=1)
    panel_info = PRODUCTS[panel_key]
    
    for day_code, label in DAYS_MAP.items():
        price = panel_info["prices"][day_code]
        stock_count = len(stock_keys.get(f"{panel_key}:{day_code}", []))
        
        if stock_count > 0:
            btn_text = f"{label} - ₹{price}"
            c_data = f"buy:{panel_key}:{day_code}"
        else:
            btn_text = f"{label} - ❌ Sold Out"
            c_data = "info:sold_out"
            
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=c_data))
        
    markup.add(types.InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:open_shop"))
    return markup

def get_back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔙 Back to Menu", callback_data="nav:go_start"))
    return markup

def get_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Key", callback_data="admin:add_key"),
        types.InlineKeyboardButton("📊 View Stock", callback_data="admin:view_stock"),
        types.InlineKeyboardButton("💰 Update Price", callback_data="admin:select_price_panel")
    )
    return markup

# --- WEBHOOK ROUTES ---
@app.route('/', methods=['GET'])
def home():
    return "Bot Webhook Server Active!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return 'OK', 200
    return 'Forbidden', 403

# RAZORPAY AUTOMATIC PAYMENT WEBHOOK ROUTE
@app.route('/razorpay-webhook', methods=['POST'])
def razorpay_webhook():
    event_data = request.json
    if event_data and event_data.get('event') == 'payment_link.paid':
        payment_entity = event_data['payload']['payment_link']['entity']
        notes = payment_entity.get('notes', {})
        order_id = notes.get('order_id')

        if order_id in pending_orders:
            order_info = pending_orders[order_id]
            u_id = order_info['user_id']
            p_key = order_info['p_key']
            d_code = order_info['d_code']
            target_stock = f"{p_key}:{d_code}"

            if len(stock_keys[target_stock]) > 0:
                key = stock_keys[target_stock].pop(0)
                game_name = PRODUCTS[p_key]['name']
                duration_str = DAYS_MAP.get(d_code, d_code.upper())

                delivery_msg = (
                    f"✅ **Auto-Payment Received!**\n\n"
                    f"🎮 **Game:** {game_name}\n"
                    f"⌛ **Duration:** {duration_str}\n"
                    f"🔑 **Key:** `{key}`\n"
                    f"🙏 **Thank you for your purchase!**\n\n"
                    f"All apk DM pe mileinge @HassanXMods1"
                )
                
                bot.send_message(u_id, delivery_msg, parse_mode="Markdown")
                
                if u_id not in user_orders:
                    user_orders[u_id] = []
                user_orders[u_id].append(f"📦 Order: `{order_id}`\nGame: {game_name}\nDuration: {duration_str}\nKey: `{key}`")

                # Notify Admin of Auto Sale
                bot.send_message(
                    PRIMARY_ADMIN_ID, 
                    f"⚡ **AUTO SALE COMPLETED!**\n\nOrder: `{order_id}`\nPanel: {game_name}\nUser ID: `{u_id}`\nKey Sent: `{key}`",
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(u_id, "⚠️ Payment verified, but stock was empty! Please contact support @HassanXMods1")
                bot.send_message(PRIMARY_ADMIN_ID, f"🚨 **AUTO SALE FAILED (NO STOCK)!**\nUser `{u_id}` paid for `{order_id}` but stock was empty!")

            del pending_orders[order_id]

    return jsonify({"status": "ok"}), 200

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.chat.id] = None
    bot.send_message(message.chat.id, WELCOME_TEXT, reply_markup=get_start_inline_menu())

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🛠️ **Admin Control Panel**", parse_mode="Markdown", reply_markup=get_admin_panel())
    else:
        bot.send_message(message.chat.id, "❌ **Access Denied!**")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    message_id = call.message.message_id
    data = call.data.split(":")
    action = data[0]

    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if action == "nav":
        sub = data[1]
        if sub == "open_shop":
            bot.edit_message_text("🛒 **Select Your Mod Panel:**", chat_id, message_id, parse_mode="Markdown", reply_markup=get_main_panel_inline())
        elif sub == "go_start":
            bot.edit_message_text(WELCOME_TEXT, chat_id, message_id, reply_markup=get_start_inline_menu())

    elif action == "user":
        sub = data[1]
        if sub == "profile":
            text = f"👤 **Profile Info**\n\nName: {call.from_user.first_name}\nUsername: @{call.from_user.username or 'None'}\nID: `{user_id}`"
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_button())
        elif sub == "purchases":
            if chat_id in user_orders and user_orders[chat_id]:
                orders_txt = "\n\n".join(user_orders[chat_id])
                text = f"🔑 **Your Active Orders:**\n\n{orders_txt}"
            else:
                text = "🔑 **Your Orders:**\n\nYou haven't made any purchases yet."
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_button())
        elif sub == "support":
            text = (
                "🎧 **Support Center**\n\n"
                "👤 Telegram: @HassanXMods1\n"
                "If you need any help, contact us on Telegram, explain your issue, and please wait for our reply."
            )
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_button())

    elif action == "info":
        if data[1] == "sold_out":
            bot.answer_callback_query(call.id, "This category is currently Sold Out!", show_alert=True)
        elif data[1] == "how_to_buy":
            text = (
                "❓ **How to Use — Tutorial Video**\n\n"
                "1. Click Shop Now.\n"
                "2. Select product & validity.\n"
                "3. Pay via Auto Razorpay Link.\n"
                "4. Get Instant Key Delivery automatically!\n\n"
                "Tap button below if you need more help!"
            )
            bot.edit_message_text(text, chat_id, message_id, parse_mode="Markdown", reply_markup=get_back_button())

    elif action == "select":
        panel_key = data[1]
        bot.edit_message_text(f"🛒 Select Category for **{PRODUCTS[panel_key]['name']}**:", chat_id, message_id, parse_mode="Markdown", reply_markup=get_category_inline(panel_key))

    elif action == "buy":
        p_key, d_code = data[1], data[2]
        price = PRODUCTS[p_key]["prices"][d_code]
        p_name = PRODUCTS[p_key]["name"]

        random_id = "".join(random.choices(string.digits, k=10))
        order_id = f"ORD-{random_id}"

        pending_orders[order_id] = {
            "user_id": chat_id,
            "p_key": p_key,
            "d_code": d_code
        }

        payment_link = create_razorpay_payment_link(
            price, 
            f"{p_name} ({d_code.upper()})", 
            call.from_user.first_name, 
            order_id
        )

        if payment_link:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💳 Pay Now (Auto Delivery)", url=payment_link))
            markup.add(types.InlineKeyboardButton("🔙 Back to Shop", callback_data="nav:open_shop"))

            payment_text = (
                f"👑 💳 — **Hassan X Mod Store** — 👑\n\n"
                f"Panel: **{p_name}**\nCategory: **{d_code.upper()}**\nPrice: **₹{price}**\n\n"
                f"⚡ Click the button below to pay via Razorpay (UPI / Cards / Wallets).\n"
                f"Key will be delivered automatically after payment!"
            )
            bot.edit_message_text(payment_text, chat_id, message_id, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(chat_id, "❌ Error generating payment link. Please try again or contact support.")

    elif action == "admin":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
            return

        sub_action = data[1]
        if sub_action == "add_key":
            markup = types.InlineKeyboardMarkup(row_width=1)
            for p_key, p_val in PRODUCTS.items():
                for d_code in ["1d", "3d", "7d", "15d", "30d"]:
                    markup.add(types.InlineKeyboardButton(f"{p_val['name']} ({d_code})", callback_data=f"admin:addstock:{p_key}:{d_code}"))
            bot.send_message(chat_id, "Select Panel & Plan to Add Key:", reply_markup=markup)

        elif sub_action == "addstock":
            p_key, d_code = data[2], data[3]
            user_states[chat_id] = f"ADDING_KEY:{p_key}:{d_code}"
            bot.send_message(chat_id, f"📝 Send the key now for **{PRODUCTS[p_key]['name']} ({d_code})**:", parse_mode="Markdown")

        elif sub_action == "view_stock":
            msg = "📊 **Current Stock & Prices:**\n\n"
            for p_key, p_val in PRODUCTS.items():
                msg += f"**{p_val['name']}**:\n"
                for d_code in ["1d", "3d", "7d", "15d", "30d"]:
                    cnt = len(stock_keys.get(f"{p_key}:{d_code}", []))
                    prc = p_val["prices"][d_code]
                    msg += f" • {d_code}: `{cnt}` Keys | ₹{prc}\n"
                msg += "\n"
            bot.send_message(chat_id, msg, parse_mode="Markdown")

        elif sub_action == "select_price_panel":
            markup = types.InlineKeyboardMarkup(row_width=1)
            for p_key, p_val in PRODUCTS.items():
                for d_code in ["1d", "3d", "7d", "15d", "30d"]:
                    curr_price = p_val["prices"][d_code]
                    markup.add(types.InlineKeyboardButton(f"{p_val['name']} ({d_code}) - ₹{curr_price}", callback_data=f"admin:editprice:{p_key}:{d_code}"))
            bot.send_message(chat_id, "💰 Select Plan to Change Price:", reply_markup=markup)

        elif sub_action == "editprice":
            p_key, d_code = data[2], data[3]
            curr_p = PRODUCTS[p_key]["prices"][d_code]
            user_states[chat_id] = f"UPDATING_PRICE:{p_key}:{d_code}"
            bot.send_message(chat_id, f"🔢 Current price for **{PRODUCTS[p_key]['name']} ({d_code})** is **₹{curr_p}**.\n\nPlease type and send the **NEW PRICE** (only numbers):", parse_mode="Markdown")

# --- TEXT / PHOTO HANDLER ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_inputs(message):
    chat_id = message.chat.id
    current_state = user_states.get(chat_id)

    if not current_state:
        return

    if current_state.startswith("UPDATING_PRICE:"):
        if not is_admin(chat_id):
            return

        _, p_key, d_code = current_state.split(":")
        new_price_text = message.text.strip() if message.text else ""

        if new_price_text.isdigit():
            new_price = int(new_price_text)
            PRODUCTS[p_key]["prices"][d_code] = new_price
            user_states[chat_id] = None
            bot.send_message(chat_id, f"✅ **Price Updated Successfully!**\n\n{PRODUCTS[p_key]['name']} ({d_code}) is now **₹{new_price}**", parse_mode="Markdown", reply_markup=get_admin_panel())
        else:
            bot.send_message(chat_id, "❌ Invalid input! Please enter numbers only (e.g. 120):")
        return

    if current_state.startswith("ADDING_KEY:"):
        if not is_admin(chat_id):
            return

        _, p_key, d_code = current_state.split(":")
        target_stock = f"{p_key}:{d_code}"
        key = message.text.strip() if message.text else ""

        if key:
            stock_keys[target_stock].append(key)
            user_states[chat_id] = None
            bot.send_message(chat_id, f"✅ **Key added to {PRODUCTS[p_key]['name']} ({d_code})!**\n\nTotal Stock Now: {len(stock_keys[target_stock])}", parse_mode="Markdown", reply_markup=get_admin_panel())
        return

# --- WEBHOOK SETTER ---
if __name__ == "__main__":
    WEBHOOK_URL = f"https://my-telegram-bot-kamx.onrender.com/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
