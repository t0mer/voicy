import os
import io
import soundfile
from wavinfo import WavInfoReader
from google.cloud import speech
from loguru import logger
from pydub import AudioSegment

class VoiceHandler():
    def __init__(self,config):
        self.config = config
        self.speech_language = self.config.get("GOOGLE","speech.language")
        self.client = speech.SpeechClient()


    #Get audio file extention
    def getExtention(self, audio_file):
        logger.info("Getting audio file extention")
        filename, file_extension = os.path.splitext(audio_file)
        return filename, file_extension

    # Convert to wav if needed
    def convertToWav(self, audio_file):
        logger.info("Input File:" +  audio_file)
        filename, file_extension = self.getExtention(audio_file)
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
    def configure_speech(self, language_code, audio_file, channel_count,sample_rate):
        config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz = sample_rate,
        audio_channel_count=int(channel_count),
        language_code=language_code,)
        return config

    # Reading audio file
    def get_audio_from_file(self, audio_file_path):
        logger.info("Reading audio file")
        with io.open(audio_file_path, "rb") as audio_file:
            content = audio_file.read()
        audio = speech.RecognitionAudio(content=content)
        return audio

    def transcript(self, command_file):
        voice_file = self.convertToWav(command_file)
        info = WavInfoReader(voice_file)
        config = self.configure_speech(self.speech_language, voice_file, info.fmt.channel_count, info.fmt.sample_rate)
        audio = self.get_audio_from_file(voice_file)
        response = self.client.recognize(request={"config": config, "audio": audio})
        transcript = str(response.results[0].alternatives[0].transcript)
        logger.info(transcript)
        os.remove(voice_file)
        return transcript