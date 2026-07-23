import os
import random
import string
from flask import Flask, request
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_IDS = [7172828025, 8705494010]
PRIMARY_ADMIN_ID = 7172828025

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- PRODUCTS CONFIG ---
PRODUCTS = {
    "main_id": {
        "name": "🛡 MAIN ID PANEL",
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

# --- KEYBOARDS ---
def get_user_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏠 Main Menu", "🛒 My Purchases", "👤 Profile", "💬 Support")
    return markup

def get_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Key", callback_data="admin:add_key"),
        types.InlineKeyboardButton("📊 View Stock", callback_data="admin:view_stock")
    )
    return markup

def get_main_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 MAIN ID PANEL", callback_data="select:main_id"),
        types.InlineKeyboardButton("💧 PRIME HOOK", callback_data="select:prime"),
        types.InlineKeyboardButton("🔺 DRIP CLIENT", callback_data="select:drip"),
        types.InlineKeyboardButton("📖 How to Buy", callback_data="info:how_to_buy")
    )
    return markup

def get_category_inline(panel_key):
    markup = types.InlineKeyboardMarkup(row_width=1)
    panel_info = PRODUCTS[panel_key]
    days_map = {"1d": "1 Day", "3d": "3 Days", "7d": "7 Days", "15d": "15 Days", "30d": "30 Days"}
    
    for day_code, label in days_map.items():
        price = panel_info["prices"][day_code]
        stock_count = len(stock_keys.get(f"{panel_key}:{day_code}", []))
        
        if stock_count > 0:
            btn_text = f"{label} - ₹{price}"
            c_data = f"buy:{panel_key}:{day_code}"
        else:
            btn_text = f"{label} - ❌ Sold Out"
            c_data = "info:sold_out"
            
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=c_data))
        
    markup.add(types.InlineKeyboardButton("🔙 Go Back", callback_data="nav:go_main"))
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

# --- COMMANDS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_states[message.chat.id] = None
    text = (
        f"🎉 Welcome to 👑 — Hassan X Mod Store — 👑, {message.from_user.first_name}!\n\n"
        f"We sell premium keys for top mobile games.\n\n"
        f"🤖 Choose a panel below to browse and buy:"
    )
    bot.send_message(message.chat.id, text, reply_markup=get_user_reply_keyboard())
    bot.send_message(message.chat.id, "Select Panel:", reply_markup=get_main_panel_inline())

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if is_admin(message.from_user.id):
        bot.send_message(message.chat.id, "🛠️ **Admin Control Panel**", parse_mode="Markdown", reply_markup=get_admin_panel())
    else:
        bot.send_message(message.chat.id, "❌ **Access Denied!**")

# --- USER REPLY BUTTONS ---
@bot.message_handler(func=lambda msg: msg.text == "🏠 Main Menu")
def main_menu(message):
    send_welcome(message)

@bot.message_handler(func=lambda msg: msg.text == "👤 Profile")
def user_profile(message):
    text = f"👤 **Profile**\n\nName: {message.from_user.first_name}\nUsername: @{message.from_user.username or 'None'}\nID: `{message.from_user.id}`"
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "🛒 My Purchases")
def my_purchases(message):
    chat_id = message.chat.id
    if chat_id in user_orders and user_orders[chat_id]:
        orders_txt = "\n\n".join(user_orders[chat_id])
        bot.send_message(chat_id, f"📦 **Your Purchases**\n\n{orders_txt}", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "📦 **Your Purchases**\n\nYou haven't made any purchases yet.", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "💬 Support")
def support_info(message):
    bot.send_message(message.chat.id, "📞 Contact us at @HassanXMods1 for any issues.")

# --- CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    data = call.data.split(":")
    action = data[0]

    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if action == "select":
        panel_key = data[1]
        bot.edit_message_text(f"🛒 Select Category for {PRODUCTS[panel_key]['name']}:", chat_id, call.message.message_id, reply_markup=get_category_inline(panel_key))

    elif action == "nav" and data[1] == "go_main":
        bot.edit_message_text("🤖 Choose a panel below to browse and buy:", chat_id, call.message.message_id, reply_markup=get_main_panel_inline())

    elif action == "info":
        if data[1] == "sold_out":
            bot.answer_callback_query(call.id, "This category is currently Sold Out!", show_alert=True)
        elif data[1] == "how_to_buy":
            bot.send_message(chat_id, "📖 **How to Buy:**\n1. Select a Panel.\n2. Choose Validity.\n3. Pay exact amount via QR/UPI ID.\n4. Send 12-digit UTR or Screenshot.\n5. Wait 2-5 mins for verification!")

    elif action == "buy":
        p_key, d_code = data[1], data[2]
        price = PRODUCTS[p_key]["prices"][d_code]
        p_name = PRODUCTS[p_key]["name"]

        payment_text = (
            f"👑 💳 — **Hassan X Mod Store** — 👑\n\n"
            f"Panel: {p_name}\nCategory: {d_code.upper()}\nPrice: ₹{price}\n\n"
            f"💳 **UPI ID**: `8171733966@fam`\nName: Harsaan Ali Khan\n\n"
            f"Please pay exact amount and send UTR / Screenshot here."
        )
        qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi://pay?pa=8171733966@fam&pn=Harsaan%20Ali%20Khan&am={price}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid:{p_key}:{d_code}"))
        bot.send_photo(chat_id, qr_url, caption=payment_text, parse_mode="Markdown", reply_markup=markup)

    elif action == "paid":
        p_key, d_code = data[1], data[2]
        user_states[chat_id] = f"WAITING_PROOF:{p_key}:{d_code}"
        bot.send_message(chat_id, "📸 Send your **12-digit UTR / Transaction ID** or **Screenshot** here:")

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
            msg = "📊 **Current Stock:**\n\n"
            for p_key, p_val in PRODUCTS.items():
                msg += f"**{p_val['name']}**:\n"
                for d_code in ["1d", "3d", "7d", "15d", "30d"]:
                    cnt = len(stock_keys.get(f"{p_key}:{d_code}", []))
                    msg += f" • {d_code}: `{cnt}` Keys\n"
                msg += "\n"
            bot.send_message(chat_id, msg, parse_mode="Markdown")

    elif action == "approve":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Not Authorized!", show_alert=True)
            return

        order_id, p_key, d_code = data[1], data[2], data[3]
        target_stock = f"{p_key}:{d_code}"

        if order_id in pending_orders:
            u_id = pending_orders[order_id]
            if len(stock_keys[target_stock]) > 0:
                key = stock_keys[target_stock].pop(0)
                bot.send_message(u_id, f"🎉 **Payment Approved!**\n\nKey for **{PRODUCTS[p_key]['name']} ({d_code.upper()})**:\n\n`{key}`", parse_mode="Markdown")
                
                if u_id not in user_orders:
                    user_orders[u_id] = []
                user_orders[u_id].append(f"📦 Order: `{order_id}`\nPanel: {PRODUCTS[p_key]['name']}\nPlan: {d_code.upper()}\nKey: `{key}`")

                bot.send_message(chat_id, f"✅ Order `{order_id}` Approved & Key delivered!")
            else:
                bot.send_message(chat_id, f"⚠️ Stock Empty for **{PRODUCTS[p_key]['name']} ({d_code})**! Add key using /admin first.")
            del pending_orders[order_id]

    elif action == "cancel":
        if not is_admin(user_id):
            bot.answer_callback_query(call.id, "❌ Not Authorized!", show_alert=True)
            return

        order_id = data[1]
        if order_id in pending_orders:
            u_id = pending_orders[order_id]
            bot.send_message(u_id, f"❌ **Payment Rejected**\n\nYour payment for Order `{order_id}` was rejected.\nContact support @HassanXMods1 if this is a mistake.", parse_mode="Markdown")
            bot.send_message(chat_id, f"❌ Order `{order_id}` Cancelled.")
            del pending_orders[order_id]

# --- TEXT / PHOTO HANDLER ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_inputs(message):
    chat_id = message.chat.id
    current_state = user_states.get(chat_id)

    if not current_state:
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

    if current_state.startswith("WAITING_PROOF:"):
        _, p_key, d_code = current_state.split(":")

        random_id = "".join(random.choices(string.digits, k=12))
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        order_id = f"ORD-{random_id}-{random_suffix}"

        pending_orders[order_id] = chat_id
        user_states[chat_id] = None

        bot.send_message(chat_id, f"✅ **Payment proof received!**\n\nOrder ID:\n`{order_id}`\n\nOur team will verify and deliver your key shortly.\nUpdates: @HassanXMods1", parse_mode="Markdown")

        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("✅ Approve", callback_data=f"approve:{order_id}:{p_key}:{d_code}"),
            types.InlineKeyboardButton("❌ Cancel", callback_data=f"cancel:{order_id}")
        )

        price = PRODUCTS[p_key]["prices"][d_code]
        admin_msg = (
            f"📩 **New Payment Proof!**\n\n"
            f"Order: `{order_id}`\n"
            f"Panel: {PRODUCTS[p_key]['name']}\n"
            f"Category: {d_code.upper()}\n"
            f"Amount: ₹{price}\n"
            f"User: @{message.from_user.username or 'NoUser'} (`{chat_id}`)"
        )

        if message.photo:
            bot.send_photo(PRIMARY_ADMIN_ID, message.photo[-1].file_id, caption=admin_msg, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(PRIMARY_ADMIN_ID, f"{admin_msg}\nProof/UTR: {message.text}", parse_mode="Markdown", reply_markup=markup)

# --- WEBHOOK SETTER ---
if __name__ == "__main__":
    WEBHOOK_URL = f"https://my-telegram-bot-kamx.onrender.com/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
                         
