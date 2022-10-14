
import json
import os
import time
from logging import Logger
from pathlib import Path

import Handler
from Entity.OperateInfo import OperateInfo


class SendHandler(Handler.KinesisHandler):
    def __init__(self, operateModel:str, operateInfo:OperateInfo, logger:Logger):
        self.__modelInfo = operateInfo.modelInfo[operateModel]
        self.__operateInfo = operateInfo
        self.__logger = logger
        super().__init__(self.__modelInfo, logger)
        
    def Process(self):
        self.__logger.info("Start DoSend")
        while (True):
            sendDataList = self.__GetData()
            for sendData in sendDataList:
                self.__logger.info("DoSend Work")
                sendFlag = self.DoSend(sendData[0])
                if sendFlag:
                    self.__DeleteData(sendData[1])
                time.sleep(1)
            time.sleep(5)
            
    def DoSend(self, data:dict) -> bool:
        try:
            self.__logger.info(f"Send Data: {data}")
            stream = self.describe(self.__modelInfo.streamName)
            result = self.put_record(data, stream['Shards'][0]['ShardId'])
            self.__logger.info(f"Send result:{result}")
            return True
        except Exception as ex:
            self.__logger.warning("__DoSend, ex: {0} | ".format(ex), exc_info=True)
            return False
        
    def __GetData(self) -> list[tuple[dict,str]]:
        result = []
        self.__logger.debug("Start Get Lost Packet")
        fileList = sorted(Path(self.__operateInfo.dataFolderPath.lostData).iterdir(),key=os.path.getmtime)
        if len(fileList) != 0:
            for lostData in fileList:
                self.__logger.debug("File Name: {0}".format(lostData.name))
                with open(self.__operateInfo.dataFolderPath.lostData + lostData.name, 'r') as f:
                    readData = f.read()
                    if len(readData) != 0:
                        self.__logger.debug("Get Lost Packet: {0}".format(readData))
                        readDataObject = json.loads(readData)
                        result.append((readDataObject, self.__operateInfo.dataFolderPath.lostData + lostData.name))
                    else:
                        self.__DeleteData(self.__operateInfo.dataFolderPath.lostData + lostData.name)
        self.__logger.debug("Finish Get Lost Packet")
        return result
    
    def __DeleteData(self, path:str):
        self.__logger.debug("Start Delete File")
        if path != None:
            os.remove(path)
            self.__logger.debug("Remove {0}".format(path))
        self.__logger.debug("Finish Delete File")