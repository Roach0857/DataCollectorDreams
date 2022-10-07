import abc

class IModbusClient(abc.ABC): 
    @abc.abstractmethod
    def RequestModbus(self, readCode:str, startBit:int = 0, value:int = 0) -> list:
        pass
    
    @abc.abstractmethod
    def GetFunctionCode(self) -> str:
        pass