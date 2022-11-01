import sys
from logging import Logger

from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

from Entity import *
from Handler import *
from Interface import *


class SlaveHandler(IMutual, AwsShadowHandler):
    """
    Slave GPIOInfo 
    pinA: Master Work Pin
    pinB: Master Internet Pin
    pinC: Self Work Pin
    """
    def __init__(self, awsInfo:AwsInfo, nodeInfo: NodeInfo, GPIOInfo: GPIOInfo, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        AwsShadowHandler.__init__(self, awsInfo, nodeInfo, ipcClient, logger)
        self.__nodeInfo = nodeInfo
        self.__GPIOInfo = GPIOInfo
        self.__logger = logger
        
    def Process(self) -> bool:
        if self.__CheckMaster():
            shadowRequest = {
                "state": {
                    "reported": {
                        "nodeID": self.__nodeInfo.node.id,
                        "state": True,
                        "clientDevice":{},
                        "thingName":sys.argv[1]}
                    }}
            self.UpdateShadow(shadowRequest)
            return False
        else:
            return True
    
    def __CheckMaster(self) -> bool:
        masterWorkflag = self.__GPIOInfo.pinA.Get()
        self.__logger.info("Master Work flag:{0}".format(masterWorkflag))
        if not masterWorkflag:
            return False
        masterInternetFlag = self.__GPIOInfo.pinB.Get()
        self.__logger.info("Master Internet Flag:{0}".format(masterInternetFlag))
        if not masterInternetFlag:
            return False
        return True