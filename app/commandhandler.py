from nis import match
from unittest import case
from urllib import response
from wsgiref import headers
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


    def command_exists(self, command_text, default_protocol):
        for command in self.commands['commands']:
            if command_text == str(command['text']):
                self.command = command
                return True
        logger.info("Command not found, fallback to default")
        command = {
          "name": "raw",
          "type": default_protocol,
          "topic": "voicy/raw",
          "payload": command_text
        }
        self.command = command
        return False

    def execute_by_type(self, type):
        if type=="post":
            return self.execute_post()
        elif type=="get":
            return self.execute_get()
        elif type=="mqtt":
            return self.execute_mqtt()
        else:
            return False,self.config.get("RESULTS","result.error")

    def execute(self, command_text, default_protocol='mqtt'):
        self.command_exists(command_text, default_protocol)
        return self.execute_by_type(self.command['type'])

    def execute_post(self):
        try:
            if str(self.command).find("data") !=-1 and str(self.command).find("headers")==-1:
                response = requests.post(self.command["url"],json=str(self.command["data"]))
            if str(self.command).find("data") !=-1 and str(self.command).find("headers")!=-1:
                response = requests.post(self.command["url"],headers=self.command["headers"],json=str(self.command["data"]))
            if str(self.command).find("data") ==-1 and str(self.command).find("headers")!=-1:
                response = requests.post(self.command["url"],headers=self.command["headers"])
            if response.status_code==200:
                return True,self.config.get("RESULTS","result.ok")
            else:
                return False,self.config.get("RESULTS","result.error")
        except Exception as e:
            logger.error(str(e))
            return False,self.config.get("RESULTS","result.error")

    def execute_get(self):
        logger.info("get")
        return True

    def execute_mqtt(self):
        try:
            self.mqtt.publish(str(self.command["topic"]),str(self.command["payload"]))
            return True,self.config.get("RESULTS","result.ok")
        except Exception as e:
            logger.error(str(e))
            return False,self.config.get("RESULTS","result.error")