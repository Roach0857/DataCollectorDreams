from dataclasses import dataclass


@dataclass
class TypeId:
    type:str
    id:int

class NodeInfo:
    def __init__(self, powerNumber:str, operateModel:str, box:dict, node:dict):
        self.powerNumber = powerNumber
        self.operateModel = operateModel
        self.box = TypeId(**box)
        self.node = TypeId(**node)
        