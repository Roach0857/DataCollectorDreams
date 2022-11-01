from dataclasses import dataclass


@dataclass
class DeviceInfo:
    type:str
    connectMode:str
    address:int
    flag:int
    deviceID:int
    comPort:str
    dreamsFlag:int
    
class ObjectInfo:
    def __init__(self, dreamsType:str, locationObjectID:str, device:list[dict]) -> None:
        self.dreamsType = dreamsType
        self.locationObjectID = locationObjectID        
        self.device = [DeviceInfo(**d) for d in device]