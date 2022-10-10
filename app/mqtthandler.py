from loguru import logger
import paho.mqtt.client as mqtt



class MqttHandler:
    def __init__(self, config):
        self.config = config
        self.mqtt_client = mqtt.Client("voicy")
        self.mqtt_host = config.get("MQTT","mqtt.host")
        self.mqtt_port = config.get("MQTT","mqtt.port")
        self.mqtt_user = config.get("MQTT","mqtt.username")
        self.mqtt_password = config.get("MQTT","mqtt.password")
        self.connect()



    #Check Connection Status
    def on_connect(self, mqtt_client, userdata, flags, rc):
        if rc==0:
            mqtt_client.connected_flag=True #set flag
            logger.info("Connected to MQTT Broker")
            mqtt_client.info("connected OK Returned code=" + str(rc))
        else:
            if rc==1:
                logger.error("Connection refused – incorrect protocol version")
            if rc==2:
                logger.error("Connection refused – invalid client identifier")
            if rc==3:
                logger.error("Connection refused – server unavailable")
            if rc==4:
                logger.error("Connection refused – bad username or password")
            if rc==5:
                logger.error("Connection refused – not authorised")

    #On MQTT disconnect event        
    def on_disconnect(self, mqtt_client, userdata, rc):
        logger.info("disconnecting reason  "  +str(rc))
        if rc==1:
            logger.error("Connection refused – incorrect protocol version")
        if rc==2:
            logger.error("Connection refused – invalid client identifier")
        if rc==3:
            logger.error("Connection refused – server unavailable")
        if rc==4:
            logger.error("Connection refused – bad username or password")
        if rc==5:
            logger.error("Connection refused – not authorised")

        mqtt_client.connected_flag=False
        mqtt_client.disconnect_flag=True
        mqtt_client.connect(self.mqtt_host)

    def is_mqtt_configured(self):
        try:
            if not self.mqtt_host or not self.mqtt_port or not self.mqtt_user or not self.mqtt_password:
                logger.info(self.mqtt_host)
                logger.info("MQTT details are missing")
                return False
            return True
        except Exception as e:
            logger.error("Mqtt configuration Error: " + str(e))
            return False

    #Setup MQTT connection
    def connect(self):
        try:
            if self.is_mqtt_configured():
                #Setting up MqttClient
                self.mqtt_client.username_pw_set(self.mqtt_user,self.mqtt_password)
                self.mqtt_client.on_connect=self.on_connect
                self.mqtt_client.on_disconnect=self.on_disconnect
                logger.info("Connecting to broker")
                mqtt.Client.connected_flag=False#create flag in class
                self.mqtt_client.connect(self.mqtt_host, keepalive=3600)
                self.mqtt_client.loop_forever()
                
            else:
                logger.info("Mqtt broker is not connected")
        except Exception as e:
            return False

    def publish(self,topic,payload):
        try:
            self.mqtt_client.publish(topic,payload,qos=0,retain=False)

        except Exception as e:
            logger.error(str(e))