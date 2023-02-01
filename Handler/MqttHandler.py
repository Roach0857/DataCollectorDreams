
import json
from logging import Logger
from Entity.DeviceConfig import DeviceConfig
from Entity.MqttInfo import MqttInfo
from Entity.NodeInfo import NodeInfo
from Entity.ObjectInfo import DeviceInfo
from Handler.DreamsHandler import DreamsHandler
from Handler.DeadbandHandler import DeadbandHandler
from apscheduler.schedulers.background import BackgroundScheduler
import paho.mqtt.client as mqtt
import threading as th

class MqttHandler(DreamsHandler):
    def __init__(self, 
                 thingName:str,
                 dreamsType: str, 
                 mqttInfo: MqttInfo, 
                 nodeInfo: NodeInfo,
                 deviceInfoList: list[DeviceInfo], 
                 deviceConfig: DeviceConfig, 
                 deadband: DeadbandHandler,
                 logger: Logger):
        super().__init__(dreamsType, nodeInfo.powerNumber, deviceInfoList, deviceConfig, logger)
        self.__thingName = thingName
        self.__dreamsType = dreamsType
        self.__mqttInfo = mqttInfo
        self.__nodeInfo = nodeInfo
        self.__deadband = deadband
        self.__logger = logger
        self.__client = mqtt.Client(client_id=f"awsiot-{thingName}")
        self.__client.username_pw_set(self.__mqttInfo.user, self.__mqttInfo.password)
        self.__client.on_connect = self.__on_connect
        self.__client.on_message = self.__on_message
        self.__mqttJob = th.Thread(target=self.__client.loop_forever)
        self.__mqttJob.start()
        self.__backgroundScheduler = BackgroundScheduler()
        self.__backgroundScheduler.add_job(self.__SendClass1Data, 'cron', minute='*/15', id='SelectData')
        self.__backgroundScheduler.start()
        
    def Connect(self):
        self.__client.connect(self.__mqttInfo.host, port=self.__mqttInfo.port, keepalive=10)
        self.__logger.info(f"Connecting to {self.__mqttInfo.host} with client ID lwt-{self.__thingName}...")

    def Publish(self, payload: str, classType:str):
        topic = f"rfdme/dreams/{self.__nodeInfo.powerNumber}/ai/class{classType}"
        result = self.__client.publish(topic=topic, qos=0, payload=payload)
        self.__logger.info(f"Published {topic}, result:{result}, payload:{payload}")

    def __on_connect(self):
        topic = f"rfdme/dreams/{self.__nodeInfo.powerNumber}/#"
        result = self.__client.subscribe(topic=topic, qos=0)
        self.__logger.info(f"Subscribed {topic}, result:{result}")

    def __on_message(self, topic: str, payload, dup, qos, retain, **kwargs):
        self.__logger.info(f"Received message from topic '{topic}': {payload}")
        message = json.loads(payload)
        if self.__dreamsType == "slave":
            if 'invSet' in message:
                self.SetInv(message)
        elif self.__dreamsType == "master":
            if 'queryID' in message:
                aiData = self.GetAIData("0", message, self.__deadband.currentData.__dict__, self.__deadband.deadbandSet.__dict__)
                self.Publish(aiData, "0")
            else:
                if 'invSet' in message:
                    self.SetInv(message)
                if 'deadbandSet' in message:
                    self.__deadband.Set(message['deadbandSet'])
                aiData = self.GetAIData("2", message, self.__deadband.currentData.__dict__, self.__deadband.deadbandSet.__dict__)
                self.Publish(aiData, "2")

    def __SendClass1Data(self):
        if self.__dreamsType == "master":
            aiData = self.GetAIData("1", currentData = self.__deadband.currentData.__dict__,  deadbandSet = self.__deadband.deadbandSet.__dict__)
            self.Publish(aiData, "1")