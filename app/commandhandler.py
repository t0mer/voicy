from nis import match
from unittest import case
import mqtthandler
from loguru import logger
import yaml
import requests

class CommandHandler:
    def __init__(self, config):
        self.config = config
        self.mqtt= mqtthandler.MqttHandler(config)
        self.commands = self.read_commands_file()
        self.command={}

    def read_commands_file(self):
        with open("config/commands.yaml",'r',encoding='utf-8') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(exc)
                return []


    def command_exists(self, command_text):
        for command in self.commands['commands']:
            if command_text == str(command['text']):
                self.command = command
                return True
        logger.info("Command not found")
        return False

    def execute(self, command_text):
        if self.command_exists(command_text):
            type=self.command["type"]
            if type=="post":
                return self.execute_post()
            elif type=="get":
                return self.execute_get()
            elif type=="mqtt":
                return self.execute_mqtt()
            else:
                return False
                

    def execute_post(self):
        logger.info("post")
        return True

    def execute_get(self):
        logger.info("get")
        return True
            
    def execute_mqtt(self):
        logger.info("mqtt")
        return True


