from logging import Logger

from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

import Entity
import Interface


class SingleHandler(Interface.IMutual):
    def __init__(self, awsInfo: Entity.AwsInfo, nodeInfo: Entity.NodeInfo, GPIOInfo: Entity.GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
        self.__logger = logger
        
    def Process(self) -> bool:
        self.__logger.info("Internet Status:{0}".format(self.PingServer()))
        return True