import abc
import datetime
from logging import Logger
import time
from Entity.DeviceConfig import ObjectConfig
from Entity.ObjectInfo import DeviceInfo
import Entity

class ModbusAbstract(abc.ABC):
    def __init__(self, locationObjectID:str, action:str, deviceInfo:DeviceInfo, deviceConfig:Entity.DeviceConfig, logger:Logger):
        self.locationObjectID = locationObjectID
        self.action = action
        self.deviceInfo = deviceInfo
        self.__logger = logger
        self.__deviceModelDeict = {1: "ctec-03",2: "ctec-04",3: "spm-3",4: "prime",5: "SP-422",6: "JXBS-3001-TH",7: "delta",8: "kaco_1",9: "kaco_2",10: "fronius",
                                   11: "goodwe",12: "kaco_3",13: "huawei_1",14: "spm-8",15: "solaredge",16: "huawei_2",17: "cyberpower",18: "SD200"}
        self.__modelName = self.__deviceModelDeict[deviceInfo.modelID]
        self.dataConfig = deviceConfig.data[deviceInfo.type][self.__modelName]
        self.__splitConfiglist = [deviceConfig.TienJi.inv, deviceConfig.TienJi.dm]
        
    def Process(self) -> Entity.ParseData:
        modbusResult = self.ReadModbus()
        self.__logger.info(f"{self.action} modbus -> Type: {self.deviceInfo.type}, model: {self.__modelName}, address:{self.deviceInfo.address}")
        self.__logger.info(f"Result: {modbusResult}")
        readTimestamp = int(time.mktime(datetime.datetime.now().timetuple()))
        parseResult = self._ParseModbus(modbusResult)
        parseResult.data = self._CalculateData(parseResult.data)
        parseResult.data["time"] = readTimestamp
        parseResult.data["deviceID"] = self.deviceInfo.deviceID
        parseResult.data["type"] = self.deviceInfo.type
        parseResult.data["objectID"] = self.__GetObjectID()
        parseResult.err["time"] = readTimestamp
        parseResult.err["deviceID"] = self.deviceInfo.deviceID
        parseResult.err["type"] = self.deviceInfo.type
        parseResult.err["objectID"] = self.__GetObjectID()
        return parseResult
    
    @abc.abstractmethod
    def ReadModbus(self) -> list:
        pass
    
    @abc.abstractmethod
    def _ParseModbus(self, modbusResult:list) -> Entity.ParseData:
        pass
    
    @abc.abstractmethod
    def _CalculateData(self, parseResult:dict) -> dict:
        pass
    
    def __GetObjectID(self):
        for splitConfig in self.__splitConfiglist:
            for splitObjectID, splitList in splitConfig.items():
                if self.locationObjectID in splitObjectID:
                    splitinfo:list[ObjectConfig]
                    splitinfo = list(filter(lambda x: x['flag'] == str(self.deviceInfo.flag), splitList))
                    if len(splitinfo) != 0:
                        return splitinfo[0].id
        return self.locationObjectID
        
    