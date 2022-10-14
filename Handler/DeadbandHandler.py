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
            file.write(json.dumps(messageDeadbandSet, default=DataCalssJsonEncoder, indent=4))
        
    def Check(self, data: dict):
        flag = False
        # need more judge
        if data["type"] == "dm":
            for field, value in data.items():
                if field in self.aiData.__dict__:
                    if self.__CheckDeadBand(field, value):
                        flag = True
        return flag
    
    def __CheckDeadBand(self, dataField:str, dataValue:float):
        flag = False
        if self.aiData.__dict__[dataField] != None:
            if abs(self.aiData.__dict__[dataField] - dataValue) > self.deadbandSet.__dict__[dataField]:
                self.__logger.debug(f"Deadband trigger -> Field:{dataField}, Value:{dataValue}")
                flag = True
        self.aiData.__dict__[dataField] = dataValue
        return flag