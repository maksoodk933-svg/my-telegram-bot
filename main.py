import os
import random
import string
import threading
from flask import Flask
import telebot
from telebot import types

TOKEN = os.environ.get('BOT_TOKEN')
# Yahan aapki Admin Telegram User ID
ADMIN_ID = int(os.environ.get('ADMIN_ID', 7172828025)) 
ADMIN_USERNAME = "@HassanXMods1"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Data Storage (In-Memory)
stock_keys = {"main_id_1d": []}
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
        types.InlineKeyboardButton("💰 Manage Prices", callback_data="admin_prices"),
        types.InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("⚡ Wake Bot", callback_data="admin_wake"),
        types.InlineKeyboardButton("🔄 Force Restart", callback_data="admin_restart"),
        types.InlineKeyboardButton("📊 Server Status", callback_data="admin_status"),
        types.InlineKeyboardButton("⚠️ View Last Error", callback_data="admin_error")
    )
    return markup

def get_main_panel_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🎁 MAIN ID PANEL", callback_data="panel_main"),
        types.InlineKeyboardButton("💧 PRIME HOOK", callback_data="panel_prime"),
        types.InlineKeyboardButton("💧 DRIP CLIENT", callback_data="panel_drip"),
        types.InlineKeyboardButton("📖 How to Buy", callback_data="how_to_buy")
    )
    return markup

def get_category_inline():
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("1 Day - ₹100", callback_data="cat_1day"),
        types.InlineKeyboardButton("3 Days - ❌ Sold Out", callback_data="sold_out"),
        types.InlineKeyboardButton("7 Days - ❌ Sold Out", callback_data="sold_out"),
        types.InlineKeyboardButton("Go Back", callback_data="go_main")
    )
    return markup

# --- COMMANDS & ROUTES ---
@app.route('/')
def home():
    return "Bot Server is Alive!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = f"🎉 Welcome to 👑 — Hassan X Mod Store — 👑, {message.from_user.first_name}!\n\nWe sell premium mod keys for top mobile games.\n\n🤖 Choose a panel below to browse and buy:"
    bot.send_message(message.chat.id, text, reply_markup=get_user_reply_keyboard())
    bot.send_message(message.chat.id, "Select Panel:", reply_markup=get_main_panel_inline())

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == ADMIN_ID or message.from_user.username == "HassanXMods1":
        bot.send_message(message.chat.id, "🛠️ **Admin Control Panel**", parse_mode="Markdown", reply_markup=get_admin_panel())
    else:
        bot.send_message(message.chat.id, "❌ Aap admin nahi hain.")

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

# --- INLINE CALLBACKS ---
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    chat_id = call.message.chat.id
    
    if call.data == "panel_main":
        bot.edit_message_text("🛒 Select a category:", chat_id, call.message.message_id, reply_markup=get_category_inline())
    elif call.data == "sold_out":
        bot.answer_callback_query(call.id, "This item is Sold Out!", show_alert=True)
    elif call.data == "go_main":
        bot.edit_message_text("🤖 Choose a panel below to browse and buy:", chat_id, call.message.message_id, reply_markup=get_main_panel_inline())
    elif call.data == "cat_1day":
        payment_text = (
            "👑 💳 — **Hassan X Mod Store** — 👑\n\n"
            "Panel: 🎁 MAIN ID PANEL\nCategory: 1 Day\nPrice: ₹100\n\n"
            "💳 **UPI ID**: `8171733966@fam`\nName: Harsaan Ali Khan\n\n"
            "Please pay exact amount and send UTR / Payment Screenshot here."
        )
        qr_url = "https://api.qrserver.com/v1/create-qr-code/?size=250x250&data=upi://pay?pa=8171733966@fam&pn=Harsaan%20Ali%20Khan&am=100"
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ I Have Paid", callback_data="paid"))
        bot.send_photo(chat_id, qr_url, caption=payment_text, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "paid":
        admin_states[chat_id] = "WAITING_PROOF"
        bot.send_message(chat_id, "📸 Send your **12-digit UTR / Transaction ID** or **Screenshot** here:")

    # --- ADMIN CALLBACKS ---
    elif call.data == "admin_add_key" and (call.from_user.id == ADMIN_ID or call.from_user.username == "HassanXMods1"):
        admin_states[call.from_user.id] = "ADD_KEY"
        bot.send_message(call.from_user.id, "📝 **1 Day**\n\nSend the key/activation code now (one message = one key):", parse_mode="Markdown")

    elif call.data == "admin_view_stock" and (call.from_user.id == ADMIN_ID or call.from_user.username == "HassanXMods1"):
        count = len(stock_keys.get("main_id_1d", []))
        bot.send_message(call.from_user.id, f"📊 **Current Stock:**\n\n🎁 main_id_1d: `{count}` Keys available.", parse_mode="Markdown")

    elif call.data.startswith("approve_"):
        order_id = call.data.split("_")[1]
        if order_id in pending_orders:
            u_id = pending_orders[order_id]
            if stock_keys["main_id_1d"]:
                key = stock_keys["main_id_1d"].pop(0)
                bot.send_message(u_id, f"🎉 **Payment Approved!**\n\nHere is your key for **MAIN ID PANEL (1 Day)**:\n\n`{key}`", parse_mode="Markdown")
                
                # Save to user purchases
                if u_id not in user_orders:
                    user_orders[u_id] = []
                user_orders[u_id].append(f"📦 {order_id} — main/id1d\nKey: `{key}`")

                bot.send_message(call.from_user.id, f"✅ Order `{order_id}` Approved & Key delivered!")
            else:
                bot.send_message(call.from_user.id, f"⚠️ Stock Empty! Add key first using /admin")
            del pending_orders[order_id]

# --- PROOF & ADMIN KEY INPUT HANDLER ---
@bot.message_handler(content_types=['text', 'photo'])
def handle_text_inputs(message):
    chat_id = message.chat.id

    # Admin Adding Key
    if (chat_id == ADMIN_ID or message.from_user.username == "HassanXMods1") and admin_states.get(chat_id) == "ADD_KEY":
        key = message.text
        stock_keys["main_id_1d"].append(key)
        admin_states[chat_id] = None
        bot.send_message(chat_id, f"✅ **Key added to main_id_1d!**\n\nKey: `{key}`", parse_mode="Markdown", reply_markup=get_admin_panel())
        return

    # User Sending Proof
    if admin_states.get(chat_id) == "WAITING_PROOF":
        random_id = "".join(random.choices(string.digits, k=12))
        random_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        order_id = f"ORD-{random_id}-{random_suffix}"
        pending_orders[order_id] = chat_id
        admin_states[chat_id] = None

        # User Confirmation
        bot.send_message(chat_id, f"✅ **Payment proof received!**\n\nOrder ID:\n`{order_id}`\n\nOur team will verify and deliver your key within a few minutes.\nFor status updates:\n{ADMIN_USERNAME}", parse_mode="Markdown")

        # Notify Admin with Approve Button
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"✅ Approved — Order {order_id}", callback_data=f"approve_{order_id}"))
        
        admin_msg = f"📩 **New Payment Proof!**\nOrder: `{order_id}`\nUser: @{message.from_user.username or 'NoUser'} (`{chat_id}`)\nCategory: 1 Day\nAmount: ₹100"
        
        # Admin Target (ID or Username fallback)
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
    
