from dataclasses import dataclass

@dataclass
class TypeId:
    type:str
    id:int

class NodeInfo:
    def __init__(self, operateModel:str, box:dict, node:dict):
        self.operateModel = operateModel
        self.box = TypeId(**box)
        self.node = TypeId(**node)
    