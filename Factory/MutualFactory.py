from logging import Logger
import Interface
import Entity
from Entity import AwsInfo
import Handler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

def MutualFactory(awsInfo:AwsInfo, nodeInfo:Entity.NodeInfo, GPIOInfo:Entity.GPIOInfo, ipcClient:GreengrassCoreIPCClient, logger:Logger) -> Interface.IMutual:
    factory = {
        "dual":{
            "master":Handler.MasterHandler, 
            "slave":Handler.SlaveHandler
            }, 
        "single":{
            "master":Handler.SingleHandler
            }}
    try:
        if nodeInfo.box.type in factory:
            return factory[nodeInfo.box.type][nodeInfo.node.type](awsInfo, nodeInfo, GPIOInfo, ipcClient, logger)
    except Exception as ex:
        logger.warning(f"MutualFactory, ex: {ex} | ", exc_info=True)
        raise ex