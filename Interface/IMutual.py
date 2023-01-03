import abc
import os


class IMutual(abc.ABC):
    @abc.abstractmethod
    def Process(self) -> bool:
        pass
    
    def PingServer(self) -> bool:
        majorFlag = os.system('ping -c 1 www.google.com')
        backupFlag = os.system('ping -c 1 1.1.1.1')
        if ((majorFlag == 0) or (backupFlag == 0)):
            return True
        return False