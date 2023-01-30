import json
from datetime import datetime
from logging import Logger
from queue import Queue
import uuid
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

from Entity.AwsInfo import AwsInfo
from Entity.NodeInfo import NodeInfo
from Entity.ObjectInfo import DeviceInfo
from Entity.OperateInfo import OperateInfo
from Entity.ParseData import ParseData
from Handler.AwsShadowHandler import AwsShadowHandler

class DataHandler(AwsShadowHandler):
    def __init__(self, awsInfo: AwsInfo, deviceInfoList:list[DeviceInfo], nodeInfo: NodeInfo,  operateInfo:OperateInfo, ipcClient:GreengrassCoreIPCClient, sendQueue:Queue, logger: Logger):
        super().__init__(awsInfo, deviceInfoList, nodeInfo, ipcClient, logger)
        self.__dataFolderPath = operateInfo.dataFolderPath.lostData
        self.__modelInfo = operateInfo.modelInfo[nodeInfo.operateModel]
        self.__logger = logger
        self.__sendQueue = sendQueue
        self.readResult:ParseData = None
        self.systemFlag = True
        
    def SelectData(self):
        nowTime = datetime.now()
        if self.readResult != None:
            shadowRequest = self.GetShadowRequest(self.readResult)
            self.__logger.debug(f"Shadow Request: {shadowRequest}")
            self.UpdateShadow(shadowRequest)
            if nowTime.minute % self.__modelInfo.period['data'] == 0:
                self.__WriteData('data', self.readResult.data)
                self.__WriteData('err', self.readResult.err)
        self.__logger.debug("Select Data Done")
                        
    def __WriteData(self, dataType:str, data:list[dict]):
        if len(data) != 0:
            strData = json.dumps(data)
            uuidStr = str(uuid.uuid4())
            fileName = f"{dataType}_{uuidStr}"
            with open(f"{self.__dataFolderPath}{fileName}.txt", 'w') as f:
                f.write(strData)
                f.close
            self.__sendQueue.put((data, f"{self.__dataFolderPath}{fileName}.txt"))
            self.__logger.debug(f"Write Data -> File Name: {fileName}, Data{strData}")