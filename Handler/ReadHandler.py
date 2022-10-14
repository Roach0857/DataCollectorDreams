import datetime
import time
from logging import Logger

from apscheduler.schedulers.background import BackgroundScheduler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

import Entity
import Factory
import Handler
from Entity.DeviceConfig import ObjectConfig
from Entity.ObjectInfo import DeviceInfo


class ReadHandler(Handler.DataHandler):
    def __init__(self, awsMqtt:Handler.AwsMqttHandler, deadband:Handler.DeadbandHandler, locationObjectID:str, deviceInfoList: list[DeviceInfo], deviceConfig: Entity.DeviceConfig, 
                 awsInfo:Entity.AwsInfo, nodeInfo:Entity.NodeInfo, operateInfo:Entity.OperateInfo, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, operateInfo, ipcClient, logger)
        self.__awsMqtt = awsMqtt
        self.__deadband = deadband
        self.__locationObjectID = locationObjectID
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__logger = logger
        self.__splitConfiglist = [deviceConfig.TienJi.inv, deviceConfig.TienJi.dm]
        self.systemFlag = True
        self.__backgroundScheduler = BackgroundScheduler()
        self.__backgroundScheduler.add_job(self.SelectData, 'cron', minute='*', id='SelectData')
        self.__backgroundScheduler.start()
        self.__logger.info(f"init ReadHandler done")
        
    def Process(self):
        while (True):
            if self.systemFlag:
                result = []
                for deviceInfo in self.__deviceInfoList:
                    result.append(self.__ReadModbusByConfig(deviceInfo))
                self.readResult = result
            else:
                time.sleep(1)
                
    def __ReadModbusByConfig(self, deviceInfo:DeviceInfo) -> Entity.ParseData:
        modbus = Factory.ModbusClientFactory(deviceInfo, self.__logger)
        parse = Handler.ParseHandler(deviceInfo, self.__deviceConfig, self.__logger)
        readCode = modbus.GetFunctionCode()
        modbusResult = []
        for read in parse.dataConfig.read:
            modbusResult.extend(modbus.RequestModbus(readCode, read.startBit, read.length))
        self.__logger.info(f"Read modbus -> Type: {deviceInfo.type}, model: {deviceInfo.modelName}, address:{deviceInfo.address}")
        self.__logger.info(f"Result: {modbusResult}")
        readTimestamp = int(time.mktime(datetime.datetime.now().timetuple()))
        parseResult = parse.ParseModbus(modbusResult)
        parseResult.data = parse.CalculateData(parseResult.data)
        parseResult.data["time"] = readTimestamp
        parseResult.data["deviceID"] = deviceInfo.deviceID
        parseResult.data["type"] = deviceInfo.type
        parseResult.data["objectID"] = self.__GetObjectID(deviceInfo.flag)
        parseResult.err["time"] = readTimestamp
        parseResult.err["deviceID"] = deviceInfo.deviceID
        parseResult.err["type"] = deviceInfo.type
        parseResult.err["objectID"] = self.__GetObjectID(deviceInfo.flag)
        if self.__deadband.Check(parseResult.data):
            aiData = self.__awsMqtt.GetAIData(parseResult.data['flag'])
            self.__awsMqtt.Publish("ai", aiData)
        return parseResult
    
    def __GetObjectID(self, flag:int):
        for splitConfig in self.__splitConfiglist:
            for splitObjectID, splitList in splitConfig.items():
                if self.__locationObjectID in splitObjectID:
                    splitinfo:list[ObjectConfig]
                    splitinfo = list(filter(lambda x: x['flag'] == str(flag), splitList))
                    if len(splitinfo) != 0:
                        return splitinfo[0].id
        return self.__locationObjectID