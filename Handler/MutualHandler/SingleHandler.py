from logging import Logger
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from Entity.AwsInfo import AwsInfo
from Entity.GPIOInfo import GPIOInfo
from Entity.NodeInfo import NodeInfo
from Interface.IMutual import IMutual


class SingleHandler(IMutual):
    def __init__(self, awsInfo: AwsInfo, nodeInfo: NodeInfo, GPIOInfo: GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
        self.__logger = logger
        
    def Process(self) -> bool:
        self.__logger.info("Internet Status:{0}".format(self.PingServer()))
        return True