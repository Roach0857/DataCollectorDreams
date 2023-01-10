from logging import Logger
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from Entity.AwsInfo import AwsInfo
from Entity.GPIOInfo import GPIOInfo
from Entity.NodeInfo import NodeInfo
from Interface.IMutual import IMutual
from Handler.MutualHandler.MasterHandler import MasterHandler
from Handler.MutualHandler.SlaveHandler import SlaveHandler
from Handler.MutualHandler.SingleHandler import SingleHandler

def MutualFactory(awsInfo:AwsInfo, nodeInfo:NodeInfo, GPIOInfo:GPIOInfo, ipcClient:GreengrassCoreIPCClient, logger:Logger) -> IMutual:
    factory = {
        "dual":{
            "master":MasterHandler, 
            "slave":SlaveHandler
            }, 
        "single":{
            "master":SingleHandler
            }}
    try:
        if nodeInfo.box.type in factory:
            return factory[nodeInfo.box.type][nodeInfo.node.type](awsInfo, nodeInfo, GPIOInfo, ipcClient, logger)
    except Exception as ex:
        logger.warning(f"MutualFactory, ex: {ex} | ", exc_info=True)
        raise ex