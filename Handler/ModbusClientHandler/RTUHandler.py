from logging import Logger
import time
import serial
from pymodbus.client.sync import ModbusSerialClient as pyRtu
from Entity.ObjectInfo import DeviceInfo
from Interface.IModbusClient import IModbusClient

class RTUHandler(IModbusClient):
    def __init__(self, deviceInfo: DeviceInfo, logger: Logger):
        self.__deviceInfo = deviceInfo
        self.__client = pyRtu(method='rtu', port=deviceInfo.comPort, baudrate=9600, timeout=0.5, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE)
        self.__modbusFunction = {"0x03":self.__client.read_holding_registers, 
                                 "0x04":self.__client.read_input_registers, 
                                 "0x06":self.__client.write_register,
                                 "0x10":self.__client.write_registers}
        self.__logger = logger
        
    def RequestModbus(self, readCode:str, startBit:int, value:int) -> list:
        result = []
        if self.__client.connect():
            try:
                readResult = self.__modbusFunction[readCode](startBit, value, unit=self.__deviceInfo.address)
            except Exception as ex:
                self.__logger.error(f"RTUHandler, ex: {ex} | ", exc_info=True)
            if hasattr(readResult, 'registers'):
                for readConfig in readResult.registers:
                    result.append(readConfig)
            else:
                for i in range(value):
                    result.append(None)
        else:
            time.sleep(1)
        self.__client.close()
        return result        

    def GetFunctionCode(self) -> str:
        if self.__deviceInfo.connectMode in ('spm-3', 'spm-8', 'delta', 'CWS-014A'):
            return "0x04"
        else:
            return "0x03"
    
