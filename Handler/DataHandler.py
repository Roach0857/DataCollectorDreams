import json
from logging import Logger
from datetime import datetime
import Entity
import Handler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient

class DataHandler(Handler.AwsShadowHandler):
    def __init__(self, awsInfo: Entity.AwsInfo, nodeInfo: Entity.NodeInfo,  operateInfo:Entity.OperateInfo, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, ipcClient, logger)
        self.__dataFolderPath = operateInfo.dataFolderPath.lostData
        self.__modelInfo = operateInfo.modelInfo[nodeInfo.operateModel]
        self.__logger = logger
        self.readResult = None
        self.systemFlag = True
        
    def SelectData(self):
        nowTime = datetime.now()
        if self.readResult != None:
            shadowRequest = self.GetShadowRequest(self.readResult)
            self.__logger.debug(f"Shadow Request: {shadowRequest}")
            self.UpdateShadow(shadowRequest)
            if nowTime.minute % self.__modelInfo.period['data'] == 0:
                for data in self.readResult:
                    if data.flag:
                        self.__WriteData(data.data, nowTime)
                        # self.__WriteData(data.err, nowTime)
                        
    def __WriteData(self, data:dict, nowTime:datetime):
        strData = json.dumps(data)
        strTime = nowTime.strftime("%Y%m%d_%H%M%S")
        fileName = f"{data['type']}_{data['deviceID']}_{strTime}"
        self.__logger.debug(f"Write Data -> File Name: {fileName}, Data{strData}")
        with open(f"{self.__dataFolderPath}{fileName}.txt", 'w') as f:
            f.write(strData)
            f.close