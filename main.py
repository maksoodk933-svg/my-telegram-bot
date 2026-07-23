import os
from flask import Flask, request
import telebot

TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

RENDER_URL = os.environ.get('RENDER_EXTERNAL_URL')

@app.route('/')
def home():
    return "Bot Server is Alive!"

@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste! Aapka bot Render par successfully chal raha hai. 🚀")

if __name__ == "__main__":
    if RENDER_URL:
        bot.remove_webhook()
        bot.set_webhook(url=RENDER_URL + '/' + TOKEN)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
    
