from logging import Logger
import Interface
import Handler
import Entity
from Entity.ObjectInfo import DeviceInfo

class PrimeHandler(Handler.RTUHandler, Interface.IWrite):
    def __init__(self, deviceInfo: DeviceInfo, deviceConfig: Entity.DeviceConfig, logger: Logger):
        Handler.RTUHandler.__init__(self, deviceInfo, deviceConfig, logger)
        self.__writeConfig = deviceConfig.data[deviceInfo.type][deviceInfo.modelName].write
        self.__logger = logger
    
    def WritePowerFactor(self, value:int) -> bool:
        if self.__GetQmode()[0] != 1:
            if not self.__SetQmode(1):
                self.__logger.error(f"""Can Not Set Qmode -> 
                                    ComPort:{self.__deviceInfo.comPort}, 
                                    Type:{self.__deviceInfo.type}, 
                                    ModeID:{self.__deviceInfo.modelName}, 
                                    Address:{self.__deviceInfo.address}""")
                return False
        if value > 0:
            setValue = value * 10
        else:
            setValue = int(hex(((abs(value) ^ 0xffff) + 1) & 0xffff), 0)
        result = self.RequestModbus("0x06", self.__writeConfig['powerFactor'].startBit, setValue)
        if result[0] == setValue:
            return True
        else:
            return False
    
    def WriteActivePower(self, value:int) -> bool:
        if self.__GetQmode()[0] != 0:
            if not self.__SetQmode(0):
                self.__logger.error(f"""Can Not Set Qmode -> 
                                    ComPort:{self.__deviceInfo.comPort}, 
                                    Type:{self.__deviceInfo.type}, 
                                    ModeID:{self.__deviceInfo.modelName}, 
                                    Address:{self.__deviceInfo.address}""")
                return False
        result = self.RequestModbus("0x06", self.__writeConfig['activePower'].startBit, value)
        if result[0] == value:
            return True
        else:
            return False
    
    def WriteReactivePower(self, value:int) -> bool:
        if self.__GetQmode()[0] != 2:
            if not self.__SetQmode(2):
                self.__logger.error(f"""Can Not Set Qmode -> 
                                    ComPort:{self.__deviceInfo.comPort}, 
                                    Type:{self.__deviceInfo.type}, 
                                    ModeName:{self.__deviceInfo.modelName}, 
                                    Address:{self.__deviceInfo.address}""")
                return False
        if value > 0:
            setValue = value * 10
        else:
            setValue = int(hex(((abs(value) ^ 0xffff) + 1) & 0xffff), 0)
        result = self.RequestModbus("0x06", self.__writeConfig['reactivePower'].startBit, setValue)
        if result[0] == value:
            return True
        else:
            
            return False
    
    def WriteVpSet(self, value:int) -> bool:
        setValue = (value / 100) * 220
        result = self.RequestModbus("0x06", self.__writeConfig['vpSet'].startBit, setValue)
        if result[0] == setValue:
            return True
        else:
            return False
        
    def SetAutoControl(self, value:int) -> bool:
        qmode = self.__GetQmode()[0]
        if value == 1:
            if qmode != 5:
                return self.__SetQmode(5)
            else:
                self.__logger.info(f"Flag: {self.__deviceInfo.flag}, Address: {self.__deviceInfo.address}, Already Auto Control")
                return True
        else:
            if qmode == 5:
                return self.__SetQmode(0)
            else:
                self.__logger.info(f"Flag: {self.__deviceInfo.flag}, Address: {self.__deviceInfo.address}, Already Not Auto Control")
                return True
        
    def __GetQmode(self) -> list:
        return self.RequestModbus("0x03", self.__writeConfig['qMode'].startBit, self.__writeConfig['qMode'].length)
    
    def __SetQmode(self, value:int) -> bool:
        result = self.RequestModbus("0x06", self.__writeConfig['qMode'].startBit, value)
        if result == value:
            return True
        else:
            return False
    