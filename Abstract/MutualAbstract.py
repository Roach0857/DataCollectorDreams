import abc
import os
import Entity
from logging import Logger
from Entity.AwsInfo import AwsInfo
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

class MutualAbstract(abc.ABC):
    def __init__(self, awsInfo:AwsInfo, nodeInfo:Entity.NodeInfo, GPIOInfo:Entity.GPIOInfo, ipcClient:GreengrassCoreIPCClient, logger:Logger):
        self.awsInfo = awsInfo
        self.nodeInfo = nodeInfo
        self.GPIOInfo = GPIOInfo
        self.ipcClient = ipcClient
        self.logger = logger
        
    @abc.abstractmethod
    def Process(self) -> bool:
        pass
    
    def PingServer(self) -> bool:
        flag = False
        majorFlag = os.system('ping -c 1 www.google.com')
        backupFlag = os.system('ping -c 1 1.1.1.1')
        if ((majorFlag == 0) or (backupFlag == 0)):
            flag = True
        return flag