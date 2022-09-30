from logging import Logger
import Abstract
import Entity
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

class SingleHandler(Abstract.MutualAbstract):
    def __init__(self, awsInfo: Entity.AwsInfo, nodeInfo: Entity.NodeInfo, GPIOInfo: Entity.GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, GPIOInfo, ipcClient, logger)
        
    def Process(self) -> bool:
        self.logger.info("Internet Status:{0}".format(self.PingServer()))
        return True