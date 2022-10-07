import datetime
from logging import Logger
import time
import Entity
from Entity.DeviceConfig import ObjectConfig
from Entity.ObjectInfo import DeviceInfo
import Factory
import Handler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from apscheduler.schedulers.background import BackgroundScheduler

class ReadHandler(Handler.DataHandler):
    def __init__(self, locationObjectID:str, deviceInfoList: list[DeviceInfo], deviceConfig: Entity.DeviceConfig, 
                 awsInfo:Entity.AwsInfo, nodeInfo:Entity.NodeInfo, operateInfo:Entity.OperateInfo, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, operateInfo, ipcClient, logger)
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