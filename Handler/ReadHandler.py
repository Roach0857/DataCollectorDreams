import datetime
from queue import Queue
import time
from logging import Logger
from apscheduler.schedulers.background import BackgroundScheduler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from Entity.AwsInfo import AwsInfo
from Entity.DeviceConfig import DeviceConfig
from Entity.NodeInfo import NodeInfo
from Entity.ObjectInfo import DeviceInfo
from Entity.OperateInfo import OperateInfo
from Entity.ParseData import ParseData
from Handler.DataHandler import DataHandler
from Handler.DeadbandHandler import DeadbandHandler
from Handler.ParseHandler import ParseHandler
from Handler.MqttHandler import MqttHandler
from Factory.ModbusClientFactory import ModbusClientFactory

class ReadHandler(DataHandler):
    def __init__(self, 
                 locationObjectID:str, 
                 deviceInfoList: list[DeviceInfo], 
                 deviceConfig: DeviceConfig, 
                 awsInfo:AwsInfo, 
                 nodeInfo:NodeInfo, 
                 operateInfo:OperateInfo, 
                 mqtt:MqttHandler,
                 deadband:DeadbandHandler, 
                 ipcClient:GreengrassCoreIPCClient,
                 sendQueue:Queue,
                 logger: Logger):
        super().__init__(awsInfo, nodeInfo, operateInfo, ipcClient, sendQueue, logger)
        self.__locationObjectID = locationObjectID
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__mqtt = mqtt
        self.__deadband = deadband
        self.__logger = logger
        self.systemFlag = True
        self.__backgroundScheduler = BackgroundScheduler()
        self.__backgroundScheduler.add_job(self.SelectData, 'cron', minute='*', id='SelectData')
        self.__backgroundScheduler.start()
        self.__logger.info(f"init ReadHandler done")
        
    def Process(self):
        while (True):
            try:
                if self.systemFlag:
                    result = ParseData()
                    for deviceInfo in self.__deviceInfoList:
                        deviceResult, errResult = self.__ReadModbusByConfig(deviceInfo)
                        result.data.append(deviceResult)
                        result.err.append(errResult)
                        if self.__deadband.Check(deviceResult):
                            aiData = self.__mqtt.GetAIData("2", currentData=self.__deadband.currentData)
                            self.__mqtt.Publish(aiData)
                    result.data = self.__TienJiProcess(result.data)
                    self.readResult = result
                else:
                    time.sleep(1)
            except Exception as ex:
                self.__logger.warning(ex, exc_info=True)
                raise ex
                
    def __ReadModbusByConfig(self, deviceInfo:DeviceInfo) -> tuple[dict, dict]:
        try:
            modbus = ModbusClientFactory(deviceInfo, self.__logger)
            parse = ParseHandler(self.__locationObjectID, deviceInfo, self.__deviceConfig, self.__logger)
            readCode = modbus.GetFunctionCode()
            modbusResult = []
            getModbusResult = list(map(lambda x:modbusResult.extend(modbus.RequestModbus(readCode, x.startBit, x.length)), parse.dataConfig.read))
            readTimestamp = int(time.mktime(datetime.datetime.now().timetuple()))
            self.__logger.debug(f"Read modbus -> Type: {deviceInfo.type}, model: {deviceInfo.connectMode}, address:{deviceInfo.address}")
            self.__logger.debug(f"Result: {modbusResult}")
            return parse.Process(modbusResult, readTimestamp)
        except Exception as ex:
            self.__logger.warning(ex, exc_info=True)
            raise ex

    def __TienJiProcess(self, parseDataList:list[dict]) -> list[dict]:
        fieldList=["acCurrentL1","acCurrentL2","acCurrentL3","acActivePowerL1","acActivePowerL2","acActivePowerL3","acActiveEnergy","reactiveEnergy"]
        checkList = list(filter(lambda x:len(x) != 0, parseDataList)) 
        if len(checkList) != 0:
            if checkList[0]['type'] == 'dm':
                if self.__locationObjectID in self.__deviceConfig.TienJi.dm:
                    mainDmList:list[dict]
                    mainDmList = list(filter(lambda x:x['objectID'] == self.__locationObjectID, parseDataList))
                    if len(mainDmList) != 0:
                        result = []
                        lowDmList:list[dict]
                        splitInfoList = self.__deviceConfig.TienJi.dm[self.__locationObjectID]
                        lowDmList = list(filter(lambda x:x['objectID'] != self.__locationObjectID, parseDataList))
                        if len(checkList) == (len(splitInfoList) + 1):
                            mainDm = {}
                            for field, value in mainDmList[0].items():
                                if field in fieldList:
                                    totalValue = 0
                                    for lowDm in lowDmList:
                                        totalValue += lowDm[field]
                                    mainDm[field] = value - totalValue
                                else:
                                    mainDm[field] = value
                            result.append(mainDm)
                        result.extend(lowDmList)
                        return result
        return parseDataList