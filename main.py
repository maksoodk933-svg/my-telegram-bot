import os
from flask import Flask
import telebot
import threading

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Server is Alive!"

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Aapka bot Render par successfully chal raha hai. 🚀")

def start_bot():
    bot.infinity_polling(non_stop=True, timeout=60, long_polling_timeout=60)

# Background thread mein bot polling run karein
t = threading.Thread(target=start_bot)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
