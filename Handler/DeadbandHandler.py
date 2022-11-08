import dataclasses
import json
import os
from logging import Logger

from Entity import *


def DataCalssJsonEncoder(o):
    return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else json.JSONEncoder.default(o)
        
class DeadbandHandler():
    def __init__(self, dreamsType:str, logger: Logger):
        self.__dreamsType = dreamsType
        self.currentData = AIData()
        self.deadbandSet = self.__GetSetting()
        self.__logger = logger

    def __GetSetting(self) -> DeadbandSet:
        if os.path.isfile("Config/DeadbandSetting.json"):
            with open("Config/DeadbandSetting.json", "r") as file:
                fileLoad = json.loads(file.read())
                DeadbandSet(**fileLoad)
        else:
            return DeadbandSet()
    
    def Set(self, messageDeadbandSet:dict):
        self.deadbandSet = DeadbandSet(**messageDeadbandSet)
        with open("Config/DeadbandSetting.json", "w") as file:
            file.write(json.dumps(messageDeadbandSet, default=DataCalssJsonEncoder, indent=4))
        
    def Check(self, data: dict):
        if self.__dreamsType == "master":
            if data["type"] == "dm":
                getValue = list(filter(lambda x:x[0] in self.currentData.__dict__ , data.items()))
                checkValue = list(map(lambda x:self.__CheckDeadBand(x[0], x[1]), getValue))
                checkFlag = list(filter(lambda x:x == True, checkValue))
                if len(checkFlag) != 0:
                    return True
        return False
    
    def __CheckDeadBand(self, dataField:str, dataValue:float):
        flag = False
        if self.currentData.__dict__[dataField] != None:
            if abs(self.currentData.__dict__[dataField] - dataValue) > self.deadbandSet.__dict__[dataField]:
                self.__logger.debug(f"Deadband trigger -> Field:{dataField}, Value:{dataValue}")
                flag = True
        self.currentData.__dict__[dataField] = dataValue
        return flag
    
    