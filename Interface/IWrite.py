import abc


class IWrite():
    @abc.abstractmethod
    def WritePowerFactor(self, value:int) -> bool:
        """
        value:100 ~ 90 and -100 ~ -90
        """
        pass
    
    @abc.abstractmethod
    def WriteActivePower(self, value:int) -> bool:
        """
        value:10 ~ 100
        """
        pass
    
    @abc.abstractmethod
    def WriteReactivePower(self, value:int) -> bool:
        """
        value:10 ~ 100
        """
        pass
    
    @abc.abstractmethod
    def WriteVpSet(self, value:int) -> bool:
        """
        value:only 105、106 、107、108、109
        """
        pass