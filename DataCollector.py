import os
from queue import Queue
import re
import sys
import time
systemType = sys.argv[1].split("-")[1]
if systemType != "raspberry":
    import DebugGPIO as GPIO 
else:
    import RPi.GPIO as GPIO 
import logging
import threading as th
from itertools import groupby
from logging import Logger, handlers
import awsiot.greengrasscoreipc
from Entity.AwsInfo import AwsInfo
from Entity.DeviceConfig import DeviceConfig
from Entity.GPIOInfo import GPIOInfo
from Entity.LogInfo import LogInfo
from Entity.MqttInfo import MqttInfo
from Entity.NodeInfo import NodeInfo
from Entity.ObjectInfo import ObjectInfo
from Entity.OperateInfo import OperateInfo
from Handler.AwsMqttHandler import AwsMqttHandler
from Handler.DeadbandHandler import DeadbandHandler
from Handler.SendHandler import SendHandler
from Handler.ReadHandler import ReadHandler
from Handler.MqttHandler import MqttHandler
from Handler.ConfigHandler import ConfigHandler
from Factory.MutualFactory import MutualFactory

def GetLogger(logInfo:LogInfo) -> Logger:
    logger = logging.getLogger("DataCollector")
    logger.setLevel(logInfo.consoleLevel)
    logFormat = logging.Formatter('%(asctime)s - %(thread)d | %(levelname)s : %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    if not os.path.isdir(logInfo.path):
        os.makedirs(logInfo.path)
    fileLogHandler = handlers.TimedRotatingFileHandler(filename="{}DataCollector".format(logInfo.path), when="MIDNIGHT", interval=1, backupCount=7, encoding='utf-8')
    fileLogHandler.suffix = "%Y-%m-%d.log"
    fileLogHandler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")
    fileLogHandler.setFormatter(logFormat)
    fileLogHandler.setLevel(logInfo.fileLevel)
    logger.addHandler(fileLogHandler)
    streamHandler = logging.StreamHandler(sys.stdout)
    streamHandler.setLevel(logInfo.consoleLevel)
    streamHandler.setFormatter(logFormat)
    logger.addHandler(streamHandler)
    return logger

class Operation():
    def __init__(self, systemInfo:dict, settingInfo:dict, logger:Logger):
        self.mqttInfo = MqttInfo(**settingInfo["mqttInfo"])
        self.awsInfo = AwsInfo(**settingInfo["awsInfo"])
        self.nodeInfo = NodeInfo(**systemInfo["nodeInfo"])
        self.objectInfo = ObjectInfo(**systemInfo["objectInfo"])
        self.operateInfo = OperateInfo(**settingInfo["operateInfo"])
        self.deviceConfig = DeviceConfig(**settingInfo["deviceConfig"])
        self.GPIOInfo = GPIOInfo(self.nodeInfo.box.type, self.nodeInfo.node.type)
        self.logger = logger
        self.__CheckFolder(self.operateInfo.dataFolderPath.lostData)
        self.__CheckFolder(self.operateInfo.dataFolderPath.rawData)
        self.deadband = DeadbandHandler(self.objectInfo.dreamsType, logger)
        self.ipcClient = awsiot.greengrasscoreipc.connect(timeout=60.0)
        self.awsMqtt = AwsMqttHandler(sys.argv[1],self.awsInfo, self.nodeInfo, self.logger)
        self.awsMqtt.Connect()
        self.mqtt = MqttHandler(sys.argv[1], self.objectInfo.dreamsType, self.mqttInfo, self.nodeInfo, self.objectInfo.device, self.deviceConfig, self.deadband, logger)
        self.mqtt.Connect()
        self.mqtt.Subscribe()
        self.mutual = MutualFactory(self.awsInfo, self.nodeInfo, self.GPIOInfo, self.ipcClient, self.logger)
        self.sendQueue = Queue()
        self.send = SendHandler(self.nodeInfo.operateModel, self.operateInfo, self.sendQueue, self.logger)
        self.sendJob = th.Thread(target=self.send.Process)
        self.sendJob.start()
        self.logger.info("Initialize Finish")
        
    def Process(self):
        readHandlerList:list[ReadHandler]
        readHandlerList = []
        self.objectInfo.device = sorted(self.objectInfo.device, key=lambda x:x.comPort)
        for comPort, deviceInfoList in groupby(self.objectInfo.device, key=lambda x:x.comPort):
            self.logger.info(f"Build Read Handler for {comPort}")
            read = None
            read = ReadHandler(self.objectInfo.locationObjectID, 
                                       list(deviceInfoList), 
                                       self.deviceConfig, 
                                       self.awsInfo, 
                                       self.nodeInfo, 
                                       self.operateInfo,
                                       self.mqtt, 
                                       self.deadband,
                                       self.ipcClient, 
                                       self.sendQueue,
                                       self.logger)
            readHandlerList.append(read)
            readJob = th.Thread(target=read.Process)
            readJob.start()
            
        while(True):
            systemFlag = self.mutual.Process()
            for readHandler in readHandlerList:
                readHandler.systemFlag = systemFlag
            self.logger.info("System Flag:{0}".format(systemFlag))
            time.sleep(60)
            
    def __CheckFolder(self, path:str):
        if not os.path.isdir(path):
            os.makedirs(path)
        
    
if __name__ == '__main__':
    thingName = sys.argv[1]
    configHandler = ConfigHandler()
    configHandler.GetParameter(thingName)
    systemInfo = configHandler.GetInfo("Config/SystemInfo.json")
    settingInfo = configHandler.GetInfo("Config/SettingInfo.json")
    logInfo = LogInfo(**settingInfo["logInfo"])
    logger = GetLogger(logInfo)
    try:
        op = Operation(systemInfo, settingInfo, logger)
        op.Process()
    except Exception as ex:
        GPIO.cleanup()
        logger.critical("DataCollector, ex: {0} |".format(ex), exc_info=True)
        raise ex