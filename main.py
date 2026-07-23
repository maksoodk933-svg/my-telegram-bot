import os
import threading
import time
import requests
from flask import Flask
import telebot

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Server is Live and Active!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Aapka bot Render par successfully chal raha hai. 🚀")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Aapne kaha: {message.text}")

def run_bot():
    # Pehle kisi bhi purane webhook ko saaf karein
    try:
        bot.remove_webhook()
        time.sleep(1)
    except Exception as e:
        print(e)
    
    # Infinity Polling Start Karein
    print("Starting Bot Polling...")
    bot.infinity_polling(skip_pending=True, timeout=20)

if __name__ == "__main__":
    # Bot ko alag thread mein chalao
    t = threading.Thread(target=run_bot)
    t.daemon = True
    t.start()
    
    # Web server run karein
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
