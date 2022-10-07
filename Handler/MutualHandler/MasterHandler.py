from logging import Logger
import Interface
import Entity
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

class MasterHandler(Interface.IMutual):
    """
    Master GPIOInfo 
    pinA: Self Work Pin
    pinB: Self Internet Pin
    pinC: Slave Work Pin
    """
    def __init__(self, awsInfo: Entity.AwsInfo, nodeInfo: Entity.NodeInfo, GPIOInfo: Entity.GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
        self.__GPIOInfo = GPIOInfo
        self.__logger = logger
        
    def Process(self) -> bool:
        if self.PingServer():
            self.__GPIOInfo.pinB.Set(True)
            return True
        else:
            self.__GPIOInfo.pinB.Set(False)
            self.__logger.info("Ping Fialed")
            return False