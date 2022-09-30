from dataclasses import dataclass

@dataclass
class DataFolderPath:
    lostData: str
    rawData: str
    
@dataclass
class ServerInfo:
    ip: str
    port: int

@dataclass
class ModelInfo:
    streamName: str
    region: str
    period: dict[str, int]

class OperateInfo:
    def __init__(self, dataFolderPath:dict, modelInfo:dict) -> None:
        self.dataFolderPath = DataFolderPath(**dataFolderPath)
        self.modelInfo = {mK:ModelInfo(**mV) for mK,mV in modelInfo.items()}
