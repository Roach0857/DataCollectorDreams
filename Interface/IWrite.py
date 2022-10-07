import abc

class IWrite():
    @abc.abstractmethod
    def WritePowerFactor(self, value:int) -> bool:
        pass
    
    @abc.abstractmethod
    def WriteActivePower(self, value:int) -> bool:
        pass
    
    @abc.abstractmethod
    def WriteReactivePower(self, value:int) -> bool:
        pass
    
    @abc.abstractmethod
    def WriteVpSet(self, value:int) -> bool:
        pass
    
    @abc.abstractmethod
    def SetAutoControl(self, value:int) -> bool:
        pass