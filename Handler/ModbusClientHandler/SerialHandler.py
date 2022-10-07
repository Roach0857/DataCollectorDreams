import serial
from logging import Logger
import Interface
from Entity.ObjectInfo import DeviceInfo
import Handler

class SerialHandler(Interface.IModbusClient, Handler.KacoHandler):
    def __init__(self, deviceInfo: DeviceInfo, logger: Logger):
        self.__deviceInfo = deviceInfo
        self.__client = serial.Serial(port=self.__deviceInfo.comPort, baudrate=9600, timeout=0.5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE)
        Handler.KacoHandler.__init__(self, self.__client, logger)
        self.__checkCode = self.__GetCheckCode()
        self.__serialFunction = {"kaco":self.ReadKaco}
        self.__logger = logger
        
    def RequestModbus(self, readCode:str, startBit:int, value:int) -> list:
        result = []
        if self.__client.isOpen():
            self.__logger.info(f"Connect Serial {self.__client.isOpen()}")
            try:
                readResult = self.__serialFunction[readCode](self.__checkCode, self.__deviceInfo.address)
            except Exception as ex:
                self.__logger.error(f"SerialHandler, ex: {ex} | ", exc_info=True)
            if readResult != None:
                for ri in readResult:
                    result.append(float(ri))
        self.__client.close()
        return result
    
    def GetFunctionCode(self) -> str:
        if "kaco" in  self.__deviceInfo.modelName:
            return "Kaco"
    
    def __GetCheckCode(self) -> str:
        if self.__deviceInfo.modelName == "kaco_3":
            return "Standard"
        else:
            return "Generic"