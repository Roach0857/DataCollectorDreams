from logging import Logger
import Abstract
import Entity
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

class MasterHandler(Abstract.MutualAbstract):
    """
    Master GPIOInfo 
    pinA: Self Work Pin
    pinB: Self Internet Pin
    pinC: Slave Work Pin
    """
    def __init__(self, awsInfo: Entity.AwsInfo, nodeInfo: Entity.NodeInfo, GPIOInfo: Entity.GPIOInfo, ipcClient: GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, GPIOInfo, ipcClient, logger)
        
    def Process(self) -> bool:
        if self.PingServer():
            self.GPIOInfo.pinB.Set(True)
            return True
        else:
            self.GPIOInfo.pinB.Set(False)
            self.logger.info("Ping Fialed")
            return False