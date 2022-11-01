from logging import Logger

from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

from Entity import *
from Interface import *


class SingleHandler(IMutual):
    def __init__(self, awsInfo: AwsInfo, nodeInfo: NodeInfo, GPIOInfo: GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
        self.__logger = logger
        
    def Process(self) -> bool:
        self.__logger.info("Internet Status:{0}".format(self.PingServer()))
        return True