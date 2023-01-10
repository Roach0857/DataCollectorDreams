from logging import Logger
from Entity.DeviceConfig import DeviceConfig
from Entity.ObjectInfo import DeviceInfo
from Handler.ModbusClientHandler.RTUHandler import RTUHandler
from Interface.IWrite import IWrite


class DeltaHandler(RTUHandler, IWrite):
    def __init__(self, deviceInfo: DeviceInfo, deviceConfig: DeviceConfig, logger: Logger):
        RTUHandler.__init__(self, deviceInfo, deviceConfig, logger)
        self.__writeConfig = deviceConfig.data[deviceInfo.type][deviceInfo.connectMode].write
        self.__logger = logger
        
    def WriteActivePower(self, value: int) -> bool:
        if value == None:
            return True
        result = self.RequestModbus("0x06", self.__writeConfig['activePower'].startBit, value)
        if result[0] == value:
            return True
        else:
            return False
    
    def WriteReactivePower(self, value: int) -> bool:
        if value == None:
            return True
        result = self.RequestModbus("0x06", self.__writeConfig['reactivePower'].startBit, value)
        if result[0] == value:
            return True
        else:
            return False
    
    def WriteVpSet(self, value: int) -> bool:
        if value == None:
            return True
        result = self.RequestModbus("0x06", self.__writeConfig['vpSet'].startBit, value)
        if result[0] == value:
            return True
        else:
            return False