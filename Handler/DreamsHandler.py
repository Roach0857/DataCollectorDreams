import dataclasses
import json
import os
from logging import Logger

from Entity import *
from Factory import *


def DataCalssJsonEncoder(o):
    return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else json.JSONEncoder.default(o)
        

class DreamsHandler():
    def __init__(self, deviceInfoList:list[DeviceInfo], deviceConfig:DeviceConfig, logger:Logger):
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__logger = logger
        self.invSet = self.__GetInvSet(deviceInfoList)
        self.control1 = list(map(lambda x:'0', range(25)))
        self.control2 = list(map(lambda x:'0', range(25)))
    
    def __GetInvSet(self, deviceInfoList:list[DeviceInfo]) -> dict[int, InvSet]:
        if os.path.isfile("Config/InvSetting.json"):
            with open("Config/InvSetting.json", "r") as file:
                fileLoad:dict
                fileLoad = json.loads(file.read())
                return dict(map(lambda x:(x[0], InvSet(**x[1]), fileLoad.items())))
        else:
            filterDeviceInfo = list(filter(lambda x:x.type == "inv" and x.dreamsFlag != 0,deviceInfoList))
            return dict(map(lambda x:(x.dreamsFlag, InvSet()), filterDeviceInfo))
    
    def SetInv(self, invNumber:int, messageInvSet:dict):
        invSet = InvSet(**messageInvSet)
        if invNumber == 0:
            setDeviceInfo = list(filter(lambda x: x.type == "inv", self.__deviceInfoList))
        else:
            setDeviceInfo = list(filter(lambda x: x.type == "inv" and x.dreamsFlag == invNumber, self.__deviceInfoList))
        
        
    def __SaveInvSet(self):
        with open("Config/SystemInfo.json", "w") as file:
            file.write(json.dumps(self.invSet, default=DataCalssJsonEncoder, indent=4))
    
    def __SetValue(self, invNumber:int, settingValue:int, writeFunction):
        if settingValue != None:
            if writeFunction(settingValue):
                self.__SetControl(invNumber)
            else:
                return False
        return True
                    
    def __SetControl(self, invNumber:int):
        if invNumber < 26:
            self.control1[invNumber - 1] = "1"
        elif 25 < invNumber < 51:
            self.control2[invNumber - 24] = "1"
        else:
            self.__logger.info("Out of Control Number, Don't Set.")
            
    def __SetAllDevice(self, invSet:InvSet, setDeviceInfo:list[DeviceInfo]):
        list(map(lambda x: self.invSet.update({x.dreamsFlag:invSet}), setDeviceInfo))
        self.__SaveInvSet()
        checkSetting = dict(map(lambda x: (x.dreamsFlag, InvSetCheck()), setDeviceInfo))
        while(True):
            for deviceInfo in setDeviceInfo:
                modbusWriter = WriteFactory(deviceInfo, self.__deviceConfig, self.__logger)
                modbusWriter.WriteActivePower(invSet.acActivePower)
                checkSetting[deviceInfo.dreamsFlag]["acActivePower"] = self.__SetValue(deviceInfo.dreamsFlag, self.invSet[deviceInfo.dreamsFlag].acActivePower, modbusWriter.WriteActivePower)
                checkSetting[deviceInfo.dreamsFlag]["acReactivePower"] = self.__SetValue(deviceInfo.dreamsFlag, self.invSet[deviceInfo.dreamsFlag].acReactivePower, modbusWriter.WriteReactivePower)
                checkSetting[deviceInfo.dreamsFlag]["powerFactor"] = self.__SetValue(deviceInfo.dreamsFlag, self.invSet[deviceInfo.dreamsFlag].powerFactor, modbusWriter.WritePowerFactor)
                checkSetting[deviceInfo.dreamsFlag]["vpSet"] = self.__SetValue(deviceInfo.dreamsFlag, self.invSet[deviceInfo.dreamsFlag].vpSet, modbusWriter.WriteVpSet)
                checkSetting[deviceInfo.dreamsFlag]["smartSwtich"] = self.__SetValue(deviceInfo.dreamsFlag, self.invSet[deviceInfo.dreamsFlag].smartSwtich, modbusWriter.SetAutoControl)