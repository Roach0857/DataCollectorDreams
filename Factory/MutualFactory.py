from logging import Logger

from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

from Entity import *
from Handler import MutualHandler
from Interface import *


def MutualFactory(awsInfo:AwsInfo, nodeInfo:NodeInfo, GPIOInfo:GPIOInfo, ipcClient:GreengrassCoreIPCClient, logger:Logger) -> IMutual:
    factory = {
        "dual":{
            "master":MutualHandler.MasterHandler, 
            "slave":MutualHandler.SlaveHandler
            }, 
        "single":{
            "master":MutualHandler.SingleHandler
            }}
    try:
        if nodeInfo.box.type in factory:
            return factory[nodeInfo.box.type][nodeInfo.node.type](awsInfo, nodeInfo, GPIOInfo, ipcClient, logger)
    except Exception as ex:
        logger.warning(f"MutualFactory, ex: {ex} | ", exc_info=True)
        raise ex