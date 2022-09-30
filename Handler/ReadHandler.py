from logging import Logger
import Entity
from Entity.ObjectInfo import DeviceInfo
import Factory
import Handler
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from apscheduler.schedulers.background import BackgroundScheduler

class ReadHandler(Handler.DataHandler):
    def __init__(self, awsInfo:Entity.AwsInfo, nodeInfo:Entity.NodeInfo, objectInfo:Entity.ObjectInfo, operateInfo:Entity.OperateInfo,
                 deviceInfoList: list[DeviceInfo], deviceConfig: Entity.DeviceConfig, ipcClient:GreengrassCoreIPCClient, logger: Logger):
        super().__init__(awsInfo, nodeInfo, operateInfo, ipcClient, logger)
        self.__locationObjectID = objectInfo.locationObjectID
        self.__deviceInfoList = deviceInfoList
        self.__deviceConfig = deviceConfig
        self.__logger = logger
        self.systemFlag = True
        self.__backgroundScheduler = BackgroundScheduler()
        self.__backgroundScheduler.add_job(self.SelectData, 'cron', minute='*', id='SelectData')
        self.__backgroundScheduler.start()
        self.__logger.info(f"init ReadHandler done")
        
    def Process(self):
        while (True):
            if self.systemFlag:
                result = []
                for deviceInfo in self.__deviceInfoList:
                    modbusHandler = None
                    modbusHandler = Factory.ModbusFactory(self.__locationObjectID, "read", deviceInfo, self.__deviceConfig, self.__logger)
                    result.append(modbusHandler.Process())
                self.readResult = result