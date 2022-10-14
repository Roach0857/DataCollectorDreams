import dataclasses
import json
import os
from logging import Logger

import Entity
import Factory
from Entity.ObjectInfo import DeviceInfo


def DataCalssJsonEncoder(o):
    return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else json.JSONEncoder.default(o)
        

class DreamsHandler():
    def __init__(self, deviceInfoList:list[DeviceInfo], deviceConfig:Entity.DeviceConfig, logger:Logger):
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__logger = logger
        self.invSet = self.__GetInvSet(deviceInfoList)
        self.control1 = ["0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0"]
        self.control2 = ["0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0","0"]
    
    def __GetInvSet(self, deviceInfoList:list[DeviceInfo]):
        if os.path.isfile("Config/InvSetting.json"):
            with open("Config/InvSetting.json", "r") as file:
                fileLoad:dict
                fileLoad = json.loads(file.read())
                return {flag:Entity.InvSet(**invSet) for flag, invSet in fileLoad.items()}
        else:
            result = {}
            for deviceInfo in deviceInfoList:
                if deviceInfo.type == "inv":
                    result[deviceInfo.flag] = Entity.InvSet()
        return result
    
    def SetInv(self, invNumber:int, messageInvSet:dict):
        invSet = Entity.InvSet(**messageInvSet)
        deviceInfo = list(filter(lambda x: x.type == "inv" and x.flag == invNumber, self.__deviceInfoList))[0]
        modbusWriter = Factory.WriteFactory(deviceInfo, self.__deviceConfig, self.__logger)
        self.__SetValue(invNumber, invSet.acActivePower, self.invSet[invNumber].acActivePower, modbusWriter.WriteActivePower)
        self.__SetValue(invNumber, invSet.acReactivePower, self.invSet[invNumber].acReactivePower, modbusWriter.WriteReactivePower)
        self.__SetValue(invNumber, invSet.powerFactor, self.invSet[invNumber].powerFactor, modbusWriter.WritePowerFactor)
        self.__SetValue(invNumber, invSet.vpSet, self.invSet[invNumber].vpSet, modbusWriter.WriteVpSet)
        self.__SetValue(invNumber, invSet.smartSwtich, self.invSet[invNumber].smartSwtich, modbusWriter.SetAutoControl)
        self.invSet[invNumber] = invSet
        self.__SaveInvSet()
        
    def __SaveInvSet(self):
        with open("Config/SystemInfo.json", "w") as file:
            file.write(json.dumps(self.invSet, default=DataCalssJsonEncoder, indent=4))
    
    def __SetValue(self, invNumber:int, settingValue:int, currentValue:int, writeFunction):
        if settingValue != currentValue:
            writeFunction(settingValue)
            currentValue = settingValue
            self.__SetControl(invNumber)
                    
    def __SetControl(self, invNumber:int):
        if invNumber < 26:
            self.control1[invNumber - 1] = "1"
        elif 25 < invNumber < 51:
            self.control2[invNumber - 24] = "1"
        else:
            raise "Wrong INV Number!!!"