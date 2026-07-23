import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Render Variables (Dono me se koi bhi naam ho, auto pick kar lega)
TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or "8952801794:AAGcF79L2Nftwd_IUp2YiF7aLH1wWS5X8eI"
ADMIN_ID_VAL = os.getenv("ADMIN_ID", "123456789")
ADMIN_ID = int(ADMIN_ID_VAL) if str(ADMIN_ID_VAL).isdigit() else 123456789

AVAILABLE_KEYS = {
    "1_day": ["KEY-1DAY-ABC1234", "KEY-1DAY-XYZ5678"],
    "7_days": ["KEY-7DAYS-QWE1234"],
    "30_days": ["KEY-30DAYS-ASD1234"]
}

PENDING_ORDERS = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [InlineKeyboardButton("🔑 Buy Mod / VIP Key", callback_data='buy_keys')],
        [InlineKeyboardButton("🛠️ Contact Admin", callback_data='contact_admin')]
    ]
    if user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])

    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\nSelect an option from below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'buy_keys':
        keyboard = [
            [InlineKeyboardButton("1 Day Key - ₹50", callback_data='plan_1_day')],
            [InlineKeyboardButton("7 Days Key - ₹200", callback_data='plan_7_days')],
            [InlineKeyboardButton("30 Days Key - ₹500", callback_data='plan_30_days')],
            [InlineKeyboardButton("🔙 Back", callback_data='main_menu')]
        ]
        await query.edit_message_text("Choose your plan:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('plan_'):
        plan = query.data.replace('plan_', '')
        PENDING_ORDERS[user_id] = plan
        text = (
            f"📌 **Order Selected:** {plan.replace('_', ' ').title()}\n\n"
            "💳 **Payment Instructions:**\n"
            "1. Pay to UPI ID: `yourupi@okicici`\n"
            "2. Payment karne ke baad screenshot is chat me bhej dein.\n\n"
            "Admin verify karke aapko instant Key bhej dega."
        )
        keyboard = [[InlineKeyboardButton("🔙 Cancel", callback_data='buy_keys')]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'main_menu':
        keyboard = [
            [InlineKeyboardButton("🔑 Buy Mod / VIP Key", callback_data='buy_keys')],
            [InlineKeyboardButton("🛠️ Contact Admin", callback_data='contact_admin')]
        ]
        if user_id == ADMIN_ID:
            keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin_panel')])
        await query.edit_message_text("👋 Welcome! Select an option:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == 'contact_admin':
        await query.edit_message_text("📩 Support/Admin Username: @your_admin_username")

    elif query.data == 'admin_panel' and user_id == ADMIN_ID:
        stats = "\n".join([f"{k}: {len(v)} remaining" for k, v in AVAILABLE_KEYS.items()])
        text = f"⚙️ **Admin Panel**\n\n**Stock Status:**\n{stats}"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='main_menu')]]
        await query.edit_message_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data.startswith('approve_'):
        parts = query.data.split('_')
        target_user = int(parts[1])
        plan = "_".join(parts[2:])

        if AVAILABLE_KEYS.get(plan):
            key = AVAILABLE_KEYS[plan].pop(0)
            await context.bot.send_message(chat_id=target_user, text=f"✅ **Payment Verified!**\n\nYour Key: `{key}`", parse_mode="Markdown")
            await query.edit_message_text(f"✅ Approved for User `{target_user}`. Key Sent: `{key}`", parse_mode="Markdown")
        else:
            await query.edit_message_text(f"❌ Out of stock for plan `{plan}`!")

    elif query.data.startswith('reject_'):
        target_user = int(query.data.split('_')[1])
        await context.bot.send_message(chat_id=target_user, text="❌ Your payment screenshot was rejected by Admin.")
        await query.edit_message_text(f"❌ Order Rejected for User `{target_user}`.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in PENDING_ORDERS:
        plan = PENDING_ORDERS.pop(user_id)
        photo_file_id = update.message.photo[-1].file_id

        keyboard = [[InlineKeyboardButton("✅ Approve", callback_data=f'approve_{user_id}_{plan}'), InlineKeyboardButton("❌ Reject", callback_data=f'reject_{user_id}')]]
        
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption=f"📥 **New Payment Screenshot!**\n\nUser ID: `{user_id}`\nPlan Requested: `{plan}`",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        await update.message.reply_text("✅ Screenshot admin ko bhej diya gaya hai. Verification ke baad key mil jayegi!")
    else:
        await update.message.reply_text("Pehle /start karke 'Buy Key' option select karein.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
    
