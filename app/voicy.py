# -*- coding: utf-8 -*-
import os

import uuid
import io
from json import dumps
from loguru import logger
from telebot import types, TeleBot
from telebot.custom_filters import AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter
import configparser
import voicehandler
import commandhandler

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'config/key-file.json'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'

#Reading configuration file
config = configparser.RawConfigParser()
config.read('config/config.ini')

ALLOWD_IDS = config.get('Telegram','bot.allowedid')
BOT_TOKEN = config.get('Telegram','bot.token')

voice = voicehandler.VoiceHandler(config)
command = commandhandler.CommandHandler(config)
commands =[]


#Load commands from file



bot = TeleBot(BOT_TOKEN)




#Validate MQTT Configuration


#Handle start/help command
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, config.get('Telegram','bot.welcome.message'))

#Handle voice command
@bot.message_handler(content_types=['voice', 'audio'])
def function_name(message):
    command_file = "recordings/" + str(uuid.uuid4()) + ".ogg"
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    with open(command_file, 'wb') as new_file:
        new_file.write(downloaded_file)
    transcript = voice.transcript(command_file)
    command.execute(transcript, config.get('Defaults', 'default.protocol'))
    bot.reply_to(message, transcript)



#Starting the bot
if __name__ == "__main__":
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    logger.info("Voicy is running")
    bot.infinity_polling()