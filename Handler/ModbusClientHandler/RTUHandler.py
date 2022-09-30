import serial
from logging import Logger
import Abstract
import Entity
import Handler
from Entity.ObjectInfo import DeviceInfo
from pymodbus.client.sync import ModbusSerialClient as pyRtu


class RTUHandler(Abstract.ModbusAbstract, Handler.ParseHandler, Handler.CalculateHandler):
    def __init__(self, locationObjectID:str, mode:str, deviceInfo:DeviceInfo, deviceConfig:Entity.DeviceConfig, logger:Logger):
        Abstract.ModbusAbstract.__init__(self, locationObjectID, mode, deviceInfo, deviceConfig, logger)
        Handler.ParseHandler.__init__(self, deviceInfo, self.dataConfig, logger)
        Handler.CalculateHandler.__init__(self, deviceInfo, logger)
        self.client = pyRtu(method='rtu', port=self.deviceInfo.comPort, baudrate=9600, timeout=0.5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.readCode = self.__GetFunctionCode()
        self.readFunction = {"0x03":self.client.read_holding_registers, 
                             "0x04":self.client.read_input_registers, 
                             "0x06":self.client.write_register,
                             "0x10":self.client.write_registers}
        self.__logger = logger
        
    def ReadModbus(self) -> list:
        result = []
        if self.client.connect():
            self.__logger.info(f"Connect Serial {self.client.connect()}")
            for readConfig in self.dataConfig.read:
                try:
                    readResult = self.readFunction[self.readCode](readConfig.startBit, readConfig.length, unit=self.deviceInfo.address)
                except Exception as ex:
                    self.__logger.error(f"RTUHandler, ex: {ex} | ", exc_info=True)
                if hasattr(readResult, 'registers'):
                    for readConfig in readResult.registers:
                        result.append(readConfig)
                else:
                    for i in range(readConfig.length):
                        result.append(None)
        self.client.close()
        return result
    
    def _ParseModbus(self, modbusResult: list) -> Entity.ParseData:
        return self.ParseModbus(modbusResult)
    
    def _CalculateData(self, data: dict) -> dict:
        return self.CalculateData(data)
    
    def __GetFunctionCode(self) -> str:
        if self.action == "read":
            if self.deviceInfo.modelID in (3, 7, 14):
                return "0x04"
            else:
                return "0x03"
    