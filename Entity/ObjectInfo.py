from dataclasses import dataclass

@dataclass
class DeviceInfo:
    type:str
    modelName:str
    address:int
    flag:int
    deviceID:int
    comPort:str

class ObjectInfo:
    def __init__(self, locationObjectID:str, device:list[dict]) -> None:
        self.locationObjectID = locationObjectID
        self.device = [DeviceInfo(**d) for d in device]
    
    