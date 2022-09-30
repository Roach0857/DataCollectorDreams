from logging import Logger
import sys
import Entity
from Entity.AwsInfo import AwsInfo
import Handler
import Abstract
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

class SlaveHandler(Abstract.MutualAbstract, Handler.AwsShadowHandler):
    """
    Slave GPIOInfo 
    pinA: Master Work Pin
    pinB: Master Internet Pin
    pinC: Self Work Pin
    """
    def __init__(self, awsInfo:AwsInfo, nodeInfo: Entity.NodeInfo, GPIOInfo: Entity.GPIOInfo, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        Abstract.MutualAbstract.__init__(self, awsInfo, nodeInfo, GPIOInfo, ipcClient, logger)
        Handler.AwsShadowHandler.__init__(self, awsInfo, nodeInfo, ipcClient, logger)
        
    def Process(self) -> bool:
        if self.__CheckMaster():
            shadowRequest = {
                "state": {
                    "reported": {
                        "nodeID": self.nodeInfo.node.id,
                        "state": True,
                        "clientDevice":{},
                        "thingName":sys.argv[1]}
                    }}
            self.UpdateShadow(shadowRequest)
            return False
        else:
            return True
    
    def __CheckMaster(self) -> bool:
        masterWorkflag = self.GPIOInfo.pinA.Get()
        self.logger.info("Master Work flag:{0}".format(masterWorkflag))
        if not masterWorkflag:
            return False
        masterInternetFlag = self.GPIOInfo.pinB.Get()
        self.logger.info("Master Internet Flag:{0}".format(masterInternetFlag))
        if not masterInternetFlag:
            return False
        return True