# -*- coding: utf-8 -*-
import os
from loguru import logger
from telebot import types, TeleBot
from telebot.custom_filters import AdvancedCustomFilter
from telebot.callback_data import CallbackData, CallbackDataFilter
import configparser
from json import dumps
from google.cloud import translate_v2 as translate
from google.cloud import speech
import yaml, uuid, base64, os, io, wave, json
from pydub import AudioSegment
from wavinfo import WavInfoReader
import paho.mqtt.client as mqtt
import soundfile
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'key-file.json'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LANG'] = 'C.UTF-8'
#Reading cpnfiguration file

logger.info("Reading configuration from config.ini")
config = configparser.RawConfigParser()
config.read('config.ini')

ALLOWD_IDS = config.get('Telegram','bot.allowedid')
BOT_TOKEN = config.get('Telegram','bot.token')

client = speech.SpeechClient()
mqtt_client = mqtt.Client("push")
bot = TeleBot(BOT_TOKEN)


def is_mqtt_configured():
    try:
        if "" not in config.get("MQTT","mqtt.port") and "" not in config.get("MQTT","mqtt.host") and "" not in config.get("MQTT","mqtt.user") and "" not in config.get("MQTT","mqtt.password"):
            return True
        logger.info("MQTT details are missing")
        return False
    except Exception as e:
        logger.error("Mqtt configuration Error: " + str(e))
        return False

def configure_mqtt_client():
    try:
        if is_mqtt_configured():
            a=1
        else:
            a=0
    except Exception as e:
        return False


#Get audio file extention
def getExtention(audio_file):
    logger.info("Getting audio file extention")
    filename, file_extension = os.path.splitext(audio_file)
    return filename, file_extension

# Convert to wav if needed
def convertToWav(audio_file):
    logger.info("Input File:" +  audio_file)
    filename, file_extension = getExtention(audio_file)
    output_file = filename + ".wav"
    logger.info("Output File:" +  output_file)
    if file_extension == ".mp3":
        logger.info("Converting from mp3 to WAV")
        sound = AudioSegment.from_mp3(audio_file)
        sound.export(output_file, format="wav")
    if file_extension == ".ogg":
        logger.info("Converting from ogg to WAV")
        sound = AudioSegment.from_ogg(audio_file)
        sound.export(output_file, format="wav")
    if file_extension == ".mp4":
        logger.info("Converting from mp4 to WAV")
        sound = AudioSegment.from_file(audio_file, "mp4")
        sound.export(output_file, format="wav")
    if file_extension == ".wma":
        logger.info("Converting from wma to WAV")
        sound = AudioSegment.from_file(audio_file, "wma")
        sound.export(output_file, format="wav")
    if file_extension == ".aac":
        logger.info("Converting from aac to WAV")
        sound = AudioSegment.from_file(audio_file, "aac")
        sound.export(output_file, format="wav")
        logger.debug(str(data))

    logger.info("Chaniging sample rate to PCM_16")
    data, samplerate = soundfile.read(output_file)
    soundfile.write(output_file, data, samplerate, subtype='PCM_16')
    logger.info("Removing original audio file")
    os.remove(audio_file)
    return output_file


# Configuring Speech
def configure_speech(language_code, audio_file, channel_count,sample_rate):
    config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz = sample_rate,
    audio_channel_count=int(channel_count),
    language_code=language_code,)
    return config

# Reading audio file
def get_audio_from_file(audio_file_path):
    logger.info("Reading audio file")
    with io.open(audio_file_path, "rb") as audio_file:
        content = audio_file.read()
    audio = speech.RecognitionAudio(content=content)
    return audio

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
    voice_file = convertToWav(command_file)
    info = WavInfoReader(voice_file)
    config = configure_speech('iw-IL', voice_file, info.fmt.channel_count, info.fmt.sample_rate)
    audio = get_audio_from_file(voice_file)
    response = client.recognize(request={"config": config, "audio": audio})
    transcript = str(response.results[0].alternatives[0].transcript).encode()
    logger.info(transcript)
    os.remove(voice_file)
    bot.reply_to(message, transcript)







#Starting the bot
if __name__ == "__main__":
    configure_mqtt_client()
    if not os.path.exists("recordings"):
        os.makedirs("recordings")
    logger.info("Voicy is running")
    bot.infinity_polling()