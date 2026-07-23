import os
import random
import string
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = int(os.environ.get('ADMIN_ID', 7172828025)) 
ADMIN_USERNAME = "@HassanXMods1"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- PRODUCTS & PRICING CONFIG ---
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

# Key Storage
stock_keys = {
    f"{panel}_{days}": [] 
    for panel in PRODUCTS.keys() 
    for days in ["1d", "3d", "7d", "15d", "30d"]
}

pending_orders = {}
user_orders = {}
admin_states = {}

# --- KEYBOARDS ---
def get_user_reply_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🏠 Main Menu", "🛒 My Purchases", "👤 Profile", "💬 Support")
    return markup

def get_admin_panel():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("➕ Add Key", callback_data="admin_add_key"),
        types.InlineKeyboardButton("📊 View Stock", callback_data="admin_view_stock"),
        types.InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("📊 Server Status", callback_data="admin_status")
    )
    return markup

def get_main_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 MAIN ID PANEL", callback_data="select_main_id"),
        types.InlineKeyboardButton("💧 PRIME HOOK", callback_data="select_prime"),
        types.InlineKeyboardButton("🔺 DRIP CLIENT", callback_data="select_drip"),
        types.InlineKeyboardButton("📖 How to Buy", callback_data="how_to_buy")
    )
    return markup

def get_category_inline(panel_key):
    markup = types.InlineKeyboardMarkup(row_width=1)
    panel_info = PRODUCTS[panel_key]
    
    days_map = {"1d": "1 Day", "3d": "3 Days", "7d": "7 Days", "15d": "15 Days", "30d": "30 Days"}
    
    for day_code, label in days_map.items():
        price = panel_info["prices"][day_code]
        stock_count = len(stock_keys.get(f"{panel_key}_{day_code}", []))
        
        if stock_count > 0:
            btn_text = f"{label} - ₹{price}"
            c_data = f"buy_{panel_key}_{day_code}"
        else:
            btn_text = f"{label} - ❌ Sold Out"
            c_data = "sold_out"
            
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=c_data))
        
    markup.add(types.InlineKeyboardButton("🔙 Go Back", callback_data="go_main"))
    return markup

# --- ROUTES & COMMANDS ---
@app.route('/')
def home():
    return "Bot Server is Alive!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = f"🎉 Welcome to 👑 — Hassan X Mod Store — 👑, {message.from_user.first_name}!\n\nWe sell premium keys for top mobile games.\n\n🤖 Choose a panel below to browse and buy:"
    bot.send_message(message.chat.id, text, reply_markup=get_user_reply_keyboard())
    bot.send_message(message.chat.id, "Select Panel:", reply_markup=get_main_panel_inline())

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == ADMIN_ID or message.from_user.username == "HassanXMods1":
        bot.send_message(message.chat.id, "🛠️ **Admin Control Panel**", parse_mode="Markdown", reply_markup=get_admin_panel())

# --- USER BUTTONS ---
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
        orders_txt = "\n".join(user_orders[chat_id])
        bot.send_message(chat_id, f"📦 **Your Purchases**\n\n{orders_txt}", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "📦 **Your Purchases**\n\nYou haven't made any purchases yet.", parse_mode="Markdown")

@bot.message_handler(func=lambda msg: msg.text == "💬 Support")
def support_info(message):
    bot.send_message(message.chat.id, f"📞 Contact us at {ADMIN_USERNAME} for any issues.")

# --- CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data.startswith("select_"):
        panel_key = call.data.replace("select_", "")
        bot.edit_message_text(f"🛒 Select Category for {PRODUCTS[panel_key]['name']}:", chat_id, call.message.message_id, reply_markup=get_category_inline(panel_key))
        
    elif call.data == "sold_out":
        bot.answer_callback_query(call.id, "This category is currently Sold Out!", show_alert=True)
        
    elif call.data == "go_main":
        bot.edit_message_text("🤖 Choose a panel below to browse and buy:", chat_id, call.message.message_id, reply_markup=get_main_panel_inline())
        
    elif call.data.startswith("buy_"):
        _, p_key, d_code = call.data.split("_")
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
        markup.add(types.InlineKeyboardButton("✅ I Have Paid", callback_data=f"paid_{p_key}_{d_code}"))
        bot.send_photo(chat_id, qr_url, caption=payment_text, parse_mode="Markdown", reply_markup=markup)

    elif call.data.startswith("paid_"):
        _, p_key, d_code = call.data.split("_")
        admin_states[chat_id] = f"WAITING_PROOF_{p_key}_{d_code}"
        bot.send_message(chat_id, "📸 Send your **12-digit UTR / Transaction ID** or **Screenshot** here:")

    # --- ADMIN CALLBACKS ---
    elif call.data == "admin_add_key" and (call.from_user.id == ADMIN_ID or call.from_user.username == "HassanXMods1"):
        markup = types.InlineKeyboardMarkup(row_width=1)
        for p_key, p_val in PRODUCTS.items():
            for d_code in ["1d", "3d", "7d", "15d", "30d"]:
                markup.add(types.InlineKeyboardButton(f"{p_val['name']} ({d_code})", callback_data=f"addstock_{p_key}_{d_code}"))
        bot.send_message(call.from_user.id, "Select Panel & Plan to Add Key:", reply_markup=markup)

    elif call.data.startswith("addstock_"):
        _, p_key, d_code = call.data.split("_")
        admin_states[call.from_user.id] = f"ADDING_KEY_{p_key}_{d_code}"
        bot.send_message(call.from_user.id, f"📝 Send the key now for **{PRODUCTS[p_key]['name']} ({d_code})**:", parse_mode="Markdown")

    elif call.data == "admin_view_stock" and (call.from_user.id == ADMIN_ID or call.from_user.username == "HassanXMods1"):
        msg = "📊 **Current Stock:**\n\n"
        for p_key, p_val in PRODUCTS.items():
            msg += f"**{p_val['name']}**:\n"
            for d_code in ["1d", "3d", "7d", "15d", "30d"]:
                cnt = len(stock_keys.get(f"{p_key}_{d_code}", []))
                msg += f" • {d_code}: `{cnt}` Keys\n"
            msg += "\n"
        bot.send_message(call.from_user.id, msg, parse_mode="Markdown")

    elif call.data.startswith("approve_"):
        parts = call.data.split("_")
        order_id = parts[1]
        p_key = parts[2]
        d_code = parts[3]
        
        target_stock = f"{p_key}_{d_code}"
        
        if order_id in pending_orders:
            u_id = pending_orders[order_id]
            if len(stock_keys[target_stock]) > 0:
                key = stock_keys[target_stock].pop(0)
                bot.send_message(u_id, f"🎉 **Payment Approved!**\n\nKey for **{PRODUCTS[p_key]['name']} ({d_code.upper()})**:\n\n`{key}`", parse_mode="Markdown")
                
                if u_id not in user_orders:
                    user_orders[u_id] = []
                user_orders[u_id].append(f"📦 {order_id} — {p_key}/{d_code}\nKey: `{key}`")

                bot.send_message(call.from_user.id, f"✅ Order `{order_id}` Approved & Key delivered!")
            else:
                bot.send_message(call.from_user.id, f"⚠️ Stock Empty for `{target_stock}`! Add key first.")
            del pending_orders[order_id]

# --- PROOF & ADMIN KEY HANDLER ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_text_inputs(message):
    chat_id = message.chat.id
    user_state = admin_states.get(chat_id, "")

    # Admin Adding Key
    if user_state.startswith("ADDING_KEY_"):
        _, _, p_key, d_code = user_state.split("_")
        target_stock = f"{p_key}_{d_code}"
        key = message.text.strip()
        
        stock_keys[target_stock].append(key)
        admin_states[chat_id] = None
        bot.send_message(chat_id, f"✅ **Key added to {PRODUCTS[p_key]['name']} ({d_code})!**\n\nTotal Stock Now: {len(stock_keys[target_stock])}", parse_mode="Markdown", reply_markup=get_admin_panel())
        return

    # User Sending Proof
    if user_state.startswith("WAITING_PROOF_"):
        _, _, p_key, d_code = user_state.split("_")
        
        random_id = "".join(random.choices(string.digits, k=12))
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        order_id = f"ORD-{random_id}-{random_suffix}"
        
        pending_orders[order_id] = chat_id
        admin_states[chat_id] = None

        bot.send_message(chat_id, f"✅ **Payment proof received!**\n\nOrder ID:\n`{order_id}`\n\nOur team will verify and deliver your key shortly.\nUpdates: {ADMIN_USERNAME}", parse_mode="Markdown")

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"✅ Approve — {order_id}", callback_data=f"approve_{order_id}_{p_key}_{d_code}"))
        
        price = PRODUCTS[p_key]["prices"][d_code]
        admin_msg = f"📩 **New Payment Proof!**\nOrder: `{order_id}`\nPanel: {PRODUCTS[p_key]['name']}\nCategory: {d_code.upper()}\nAmount: ₹{price}\nUser: @{message.from_user.username or 'NoUser'} (`{chat_id}`)"
        
        target_admin = ADMIN_ID if ADMIN_ID else message.chat.id

        if message.photo:
            bot.send_photo(target_admin, message.photo[-1].file_id, caption=admin_msg, parse_mode="Markdown", reply_markup=markup)
        else:
            bot.send_message(target_admin, f"{admin_msg}\nProof/UTR: {message.text}", parse_mode="Markdown", reply_markup=markup)

if __name__ == "__main__":
    def run_bot():
        bot.remove_webhook()
        bot.infinity_polling(skip_pending=True)

    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
