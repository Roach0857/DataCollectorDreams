import dataclasses
import datetime
import json
import os
from logging import Logger
import time
import threading as th
from Entity.AIData import AIData
from Entity.DeviceConfig import DeviceConfig
from Entity.InvSet import InvSet
from Entity.ObjectInfo import DeviceInfo
from Factory.WriteFactory import WriteFactory

def DataCalssJsonEncoder(o):
    return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else json.JSONEncoder.default(o)
        

class DreamsHandler():
    def __init__(self, dreamsType:str, powerNumber:str, deviceInfoList:list[DeviceInfo], deviceConfig:DeviceConfig, logger:Logger):
        self.__dreamsType = dreamsType
        self.__powerNumber = powerNumber
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__logger = logger
        self.invSetDict = self.__GetInvSet(deviceInfoList)
        self.control1 = list(map(lambda x:'0', range(25)))
        self.control2 = list(map(lambda x:'0', range(25)))
    
    def __GetInvSet(self, deviceInfoList:list[DeviceInfo]) -> dict[int, InvSet]:
        if os.path.isfile("Config/InvSetting.json"):
            with open("Config/InvSetting.json", "r") as file:
                fileLoad:dict
                fileLoad = json.loads(file.read())
                return dict(map(lambda x:(x[0], InvSet(**x[1]), fileLoad.items())))
        else:
            if self.__dreamsType == "master":
                return {0:InvSet()}
            elif self.__dreamsType != None:
                filterDeviceInfo = list(filter(lambda x:x.type == "inv" and x.dreamsFlag != 0,deviceInfoList))
                return dict(map(lambda x:(x.dreamsFlag, InvSet()), filterDeviceInfo))
            else:
                return {}
            
    def SetInv(self, message:dict):
        nextInvSet:dict = message["invSet"]
        invNumber:int = message["invNumber"]
        if self.__dreamsType == "master":
            if invNumber == 0:
                self.invSetDict[0].__dict__.update(dict(filter(lambda x:x[0] in self.invSetDict[0].__dict__, nextInvSet.items())))
        elif self.__dreamsType != None:
            if invNumber == 0:
                getNextInvSet = dict(filter(lambda x:x, self.invSetDict.items()))
                setNextInvSet = list(map(lambda x:self.invSetDict[x[0]].__dict__.update(x[1]), getNextInvSet.items()))
            else:
                getNextInvSet = dict(filter(lambda x:x[0] == invNumber, self.invSetDict.items()))
                self.invSetDict[invNumber].__dict__.update(getNextInvSet[invNumber])
            setAllDevice = th.Thread(target=self.__SetAllDevice)
            setAllDevice.start()
        self.__SaveInvSet()
        
    def __SaveInvSet(self):
        with open("Config/SystemInfo.json", "w") as file:
            file.write(json.dumps(self.invSetDict, default=DataCalssJsonEncoder, indent=4))
    
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
            
    def __SetAllDevice(self):
        for dreamsFlag, invSet in self.invSetDict.items():
            deviceInfo:DeviceInfo
            deviceInfo = list(filter(lambda x:x.dreamsFlag == dreamsFlag, self.__deviceInfoList))[0]
            modbusWriter = WriteFactory(deviceInfo, self.__deviceConfig, self.__logger)
            while(True):
                flagList = []
                flagList.append(self.__SetValue(dreamsFlag, invSet.acActivePower, modbusWriter.WriteActivePower))
                flagList.append(self.__SetValue(dreamsFlag, invSet.acReactivePower, modbusWriter.WriteReactivePower))
                flagList.append(self.__SetValue(dreamsFlag, invSet.powerFactor, modbusWriter.WritePowerFactor))
                flagList.append(self.__SetValue(dreamsFlag, invSet.vpSet, modbusWriter.WriteVpSet))
                if len(list(filter(lambda x:x == False, flagList))) == 0:
                    break

    def GetAIData(self, dataClass:str = "0", message:dict = None, currentData:dict = None, deadbandSet:dict = None):
        result = {"class":dataClass}
        if dataClass == "0":
            result["powerNumber"] = message["powerNumber"]
            result["invNumber"] = message["invNumber"]
            result["queryID"] = message["queryID"]
            result.update(dict(filter(lambda x:x[0] in AIData().__dict__, currentData.items())))
            result["deadbandSet"] = deadbandSet
            result["invSet"] = self.invSetDict[0]
            result["invSet"]["control1"] = self.control1
            result["invSet"]["control2"] = self.control2
            result["timestamp"] = int(time.mktime(datetime.datetime.now().timetuple()))
        elif dataClass == "1":
            result["powerNumber"] = self.__powerNumber
            result["invNumber"] = 0
            result.update(dict(filter(lambda x:x[0] in AIData().__dict__, currentData.items())))
            result["deadbandSet"] = deadbandSet
            result["invSet"] = self.invSetDict[0]
            result["timestamp"] = int(time.mktime(datetime.datetime.now().timetuple()))
        elif dataClass == "2":
            result["powerNumber"] = self.__powerNumber
            result["invNumber"] = 0
            if currentData != None:
                result.update(dict(filter(lambda x:x[0] in AIData().__dict__, currentData.items())))
            if message != None:
                if "deadbandSet" in message:
                    result["deadbandSet"] = message['deadbandSet']
        return json.dumps(result)