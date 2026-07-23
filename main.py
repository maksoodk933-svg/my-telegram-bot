import os
import threading
from flask import Flask
import telebot

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Server is Running Live!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Aapka bot Render par successfully chal raha hai. 🚀")

def run_bot():
    bot.infinity_polling(skip_pending=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
  
