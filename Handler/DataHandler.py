import json
from datetime import datetime
from logging import Logger

from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

from Entity import *
from Handler import *


class DataHandler(AwsShadowHandler):
    def __init__(self, awsInfo: AwsInfo, nodeInfo: NodeInfo,  operateInfo:OperateInfo, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, ipcClient, logger)
        self.__dataFolderPath = operateInfo.dataFolderPath.lostData
        self.__modelInfo = operateInfo.modelInfo[nodeInfo.operateModel]
        self.__logger = logger
        self.readResult:ParseData = None
        self.systemFlag = True
        
    def SelectData(self):
        nowTime = datetime.now()
        if self.readResult != None:
            shadowRequest = self.GetShadowRequest(self.readResult)
            self.__logger.debug(f"Shadow Request: {shadowRequest}")
            self.UpdateShadow(shadowRequest)
            if nowTime.minute % self.__modelInfo.period['data'] == 0:
                self.__WriteData('data', self.readResult.data, nowTime)
                self.__WriteData('err', self.readResult.err, nowTime)
        self.__logger.debug("Select Data Done")
                        
    def __WriteData(self, dataType:str, data:list[dict], nowTime:datetime):
        if len(data) != 0:
            strData = json.dumps(data)
            strTime = nowTime.strftime("%Y%m%d_%H%M%S")
            fileName = f"{dataType}_{strTime}"
            self.__logger.debug(f"Write Data -> File Name: {fileName}, Data{strData}")
            with open(f"{self.__dataFolderPath}{fileName}.txt", 'w') as f:
                f.write(strData)
                f.close