import os,sys,re
import time
systemType = sys.argv[1].split("-")[1]
if systemType != "raspberry":
    import DebugGPIO as GPIO 
else:
    import RPi.GPIO as GPIO 
import logging
from logging import Logger,handlers
import Handler
import Entity
import Factory
import awsiot.greengrasscoreipc
import threading as th
from itertools import groupby

def GetLogger(logInfo:Entity.LogInfo) -> Logger:
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
        self.awsInfo = Entity.AwsInfo(**systemInfo["awsInfo"])
        self.nodeInfo = Entity.NodeInfo(**systemInfo["nodeInfo"])
        self.objectInfo = Entity.ObjectInfo(**systemInfo["objectInfo"])
        self.operateInfo = Entity.OperateInfo(**settingInfo["operateInfo"])
        self.deviceConfig = Entity.DeviceConfig(**settingInfo["deviceConfig"])
        self.GPIOInfo = Entity.GPIOInfo(self.nodeInfo.box.type, self.nodeInfo.node.type)
        self.logger = logger
        self.__CheckFolder(self.operateInfo.dataFolderPath.lostData)
        self.__CheckFolder(self.operateInfo.dataFolderPath.rawData)
        self.ipcClient = awsiot.greengrasscoreipc.connect(timeout=60.0)
        self.logger.info("Initialize Finish")
        
    def Process(self):
        awsLwt = Handler.AwsLwtHandler(self.awsInfo, self.nodeInfo, logger)
        awsLwt.Connect(sys.argv[1])
        mutual = Factory.MutualFactory(self.awsInfo, self.nodeInfo, self.GPIOInfo, self.ipcClient, self.logger)
        send = Handler.SendHandler(self.nodeInfo.operateModel, self.operateInfo, self.logger)
        sendJob = th.Thread(target=send.Process)
        sendJob.start()
        readHandlerList = []
        self.objectInfo.device = sorted(self.objectInfo.device, key=lambda x:x.comPort)
        for comPort, deviceInfoList in groupby(self.objectInfo.device, key=lambda x:x.comPort):
            self.logger.info(f"Build Read Handler for {comPort}")
            read = None
            read = Handler.ReadHandler(self.awsInfo, self.nodeInfo, self.objectInfo, self.operateInfo, list(deviceInfoList), self.deviceConfig, self.ipcClient, self.logger)
            readHandlerList.append(read)
            readJob = th.Thread(target=read.Process)
            readJob.start()
        count = 0
        while(True):
            self.logger.info(f"{count}")
            count += 1
            systemFlag = mutual.Process()
            for readHandler in readHandlerList:
                readHandler.systemFlag = systemFlag
            self.logger.info("System Flag:{0}".format(systemFlag))
            time.sleep(1)
            
    def __CheckFolder(self, path:str):
        if not os.path.isdir(path):
            os.makedirs(path)
        
    
if __name__ == '__main__':
    thingName = sys.argv[1]
    configHandler = Handler.ConfigHandler()
    configHandler.GetParameter(thingName)
    systemInfo = configHandler.GetInfo("Config/SystemInfo.json")
    settingInfo = configHandler.GetInfo("Config/SettingInfo.json")
    logInfo = Entity.LogInfo(**settingInfo["logInfo"])
    logger = GetLogger(logInfo)
    try:
        op = Operation(systemInfo, settingInfo, logger)
        op.Process()
    except Exception as ex:
        GPIO.cleanup()
        logger.critical("DataCollector, ex: {0} |".format(ex), exc_info=True)
        raise ex