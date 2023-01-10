from logging import Logger
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from Entity.AwsInfo import AwsInfo
from Entity.GPIOInfo import GPIOInfo
from Entity.NodeInfo import NodeInfo
from Interface.IMutual import IMutual

class MasterHandler(IMutual):
    """
    Master GPIOInfo 
    pinA: Self Work Pin
    pinB: Self Internet Pin
    pinC: Slave Work Pin
    """
    def __init__(self, awsInfo: AwsInfo, nodeInfo: NodeInfo, GPIOInfo: GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
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