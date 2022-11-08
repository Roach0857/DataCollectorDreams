import datetime
from queue import Queue
import time
from logging import Logger

from apscheduler.schedulers.background import BackgroundScheduler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

from Entity import *
from Factory import *
from Handler import *


class ReadHandler(DataHandler):
    def __init__(self, 
                 locationObjectID:str, 
                 deviceInfoList: list[DeviceInfo], 
                 deviceConfig: DeviceConfig, 
                 awsInfo:AwsInfo, 
                 nodeInfo:NodeInfo, 
                 operateInfo:OperateInfo, 
                 awsMqtt:AwsMqttHandler, 
                 deadband:DeadbandHandler, 
                 ipcClient:GreengrassCoreIPCClient,
                 sendQueue:Queue,
                 logger: Logger):
        super().__init__(awsInfo, nodeInfo, operateInfo, ipcClient, sendQueue, logger)
        self.__locationObjectID = locationObjectID
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__awsMqtt = awsMqtt
        self.__deadband = deadband
        self.__logger = logger
        self.systemFlag = True
        self.__backgroundScheduler = BackgroundScheduler()
        self.__backgroundScheduler.add_job(self.SelectData, 'cron', minute='*', id='SelectData')
        self.__backgroundScheduler.start()
        self.__logger.info(f"init ReadHandler done")
        
    def Process(self):
        while (True):
            if self.systemFlag:
                result = ParseData()
                for deviceInfo in self.__deviceInfoList:
                    parseResult = self.__ReadModbusByConfig(deviceInfo)
                    result.data.append(parseResult[0])
                    result.err.append(parseResult[1])
                    if self.__deadband.Check(parseResult[0]):
                        aiData = self.__awsMqtt.GetAIData("2", currentData=parseResult[0])
                        self.__awsMqtt.Publish(aiData)
                result.data = self.__tienJiProcess(result.data)
                self.readResult = result
            else:
                time.sleep(1)
                
    def __ReadModbusByConfig(self, deviceInfo:DeviceInfo) -> tuple[dict, dict]:
        modbus = ModbusClientFactory(deviceInfo, self.__logger)
        parse = ParseHandler(self.__locationObjectID, deviceInfo, self.__deviceConfig, self.__logger)
        readCode = modbus.GetFunctionCode()
        modbusResult = []
        modbusResult.extend(list(map(lambda x:modbus.RequestModbus(readCode, x.startBit, x.length), parse.dataConfig.read)))
        readTimestamp = int(time.mktime(datetime.datetime.now().timetuple()))
        self.__logger.info(f"Read modbus -> Type: {deviceInfo.type}, model: {deviceInfo.connectMode}, address:{deviceInfo.address}")
        self.__logger.info(f"Result: {modbusResult}")
        return parse.Process(modbusResult, readTimestamp)
    
    def __tienJiProcess(self, parseDataList:list[dict]) -> list[dict]:
        fieldList=["acCurrentL1","acCurrentL2","acCurrentL3","acActivePowerL1","acActivePowerL2","acActivePowerL3","acActiveEnergy","reactiveEnergy"]
        checkList = list(filter(lambda x:len(x) != 0, parseDataList)) 
        if len(checkList) != 0:
            if checkList[0]['type'] == 'dm':
                if self.__locationObjectID in self.__deviceConfig.TienJi.dm:
                    masterData:list[dict]
                    masterData = list(filter(lambda x:x['objectID'] == self.__locationObjectID, parseDataList))
                    if len(masterData) != 0:
                        result:list[dict]
                        objectConfig = self.__deviceConfig.TienJi.dm[self.__locationObjectID]
                        result = list(filter(lambda x:x['objectID'] != self.__locationObjectID, parseDataList))
                        if len(checkList) != (len(objectConfig) + 1):
                            return result
                        else:
                            temp = {}
                            for k, v in masterData[0].items():
                                if k in fieldList:
                                    vv = 0
                                    for r in result:
                                        vv += r[k]
                                    temp[k] = v - (vv)
                                else:
                                    temp[k] = v
                            return result
        return parseDataList