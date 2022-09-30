import serial
from logging import Logger
import Abstract
import Entity
from Entity.ObjectInfo import DeviceInfo
import Handler

class SerialHandler(Abstract.ModbusAbstract, Handler.KacoHandler, Handler.ParseHandler, Handler.CalculateHandler):
    def __init__(self, locationObjectID:str, mode:str, deviceInfo:DeviceInfo, deviceConfig:Entity.DeviceConfig, logger:Logger):
        Abstract.ModbusAbstract.__init__(self, locationObjectID, mode, deviceInfo, deviceConfig, logger)
        Handler.ParseHandler.__init__(self, deviceInfo, self.dataConfig, logger)
        Handler.CalculateHandler.__init__(self, deviceInfo, logger)
        self.client = serial.Serial(port=self.deviceInfo.comPort, baudrate=9600, timeout=0.5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
        Handler.KacoHandler.__init__(self, self.client, logger)
        self.readCode = self.__GetFunctionCode()
        self.checkCode = self.__GetCheckCode()
        self.readFunction = {"kaco":self.ReadKaco}
        self.__logger = logger
        
    def ReadModbus(self) -> list:
        result = []
        if self.client.isOpen():
            self.__logger.info(f"Connect Serial {self.client.isOpen()}")
            try:
                readResult = self.readFunction[self.readCode](self.checkCode, self.deviceInfo.address)
            except Exception as ex:
                self.__logger.error(f"SerialHandler, ex: {ex} | ", exc_info=True)
            if readResult != None:
                for ri in readResult:
                    result.append(float(ri))
        self.client.close()
        return result
    
    def _ParseModbus(self, modbusResult: list) -> Entity.ParseData:
        return self.ParseModbus(modbusResult)
    
    def _CalculateData(self, data: dict) -> dict:
        return self.CalculateData(data)
    
    def __GetFunctionCode(self) -> str:
        if self.action == "r":
            if self.deviceInfo.modelID in (8, 9, 12):
                return "Kaco"
    
    def __GetCheckCode(self) -> str:
            if self.deviceInfo.modelID in (12):
                return "Standard"
            else:
                return "Generic"