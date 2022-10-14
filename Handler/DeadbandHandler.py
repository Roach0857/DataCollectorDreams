import dataclasses
import json
import os
from logging import Logger

import Entity


def DataCalssJsonEncoder(o):
    return dataclasses.asdict(o) if dataclasses.is_dataclass(o) else json.JSONEncoder.default(o)
        
class DeadbandHandler():
    def __init__(self, logger: Logger):
        self.aiData = Entity.AIData()
        self.deadbandSet = self.__GetSetting()
        self.__logger = logger

    def __GetSetting(self) -> Entity.DeadbandSet:
        if os.path.isfile("Config/DeadbandSetting.json"):
            with open("Config/DeadbandSetting.json", "r") as file:
                fileLoad = json.loads(file.read())
                Entity.DeadbandSet(**fileLoad)
        else:
            return Entity.DeadbandSet()
    
    def Set(self, messageDeadbandSet:dict):
        self.deadbandSet = Entity.DeadbandSet(**messageDeadbandSet)
        with open("Config/DeadbandSetting.json", "w") as file:
            file.write(json.dumps(messageDeadbandSet, indent=4))
        
    def Check(self, data: dict):
        flag = False
        # need more judge
        if data["type"] == "dm":
            for dataField, dataValue in data.items():
                if self.__CheckDeadBand(dataField, dataValue):
                    self.__logger.debug(f"Deadband trigger -> deviceID:{data['deviceID']}, Field:{dataField}, Value:{dataValue}")
                    flag = True
        return flag
    
    def __CheckDeadBand(self, dataField:str, dataValue:float) -> bool:
        flag = False
        if self.aiData[dataField] != None:
            if abs(self.aiData[dataField] - dataValue) > self.deadbandSet[dataField]:
                flag = True
        self.aiData[dataField] = dataValue
        return flag
    