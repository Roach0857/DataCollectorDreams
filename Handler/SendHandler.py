
import json
import os
from queue import Queue
import time
from logging import Logger
from pathlib import Path

from Entity import *
from Handler import *


class SendHandler(KinesisHandler):
    def __init__(self, operateModel:str, operateInfo:OperateInfo, sendQueue:Queue, logger:Logger):
        self.__modelInfo = operateInfo.modelInfo[operateModel]
        self.__operateInfo = operateInfo
        self.__sendQueue = sendQueue
        self.__logger = logger
        super().__init__(self.__modelInfo, logger)
        self.__GetData()
        
    def Process(self):
        self.__logger.info("Start DoSend")
        while (True):
            if not self.__sendQueue.empty():
                self.__logger.info("DoSend Work")
                sendData = self.__sendQueue.get()
                if self.DoSend(sendData[0]):
                    self.__DeleteData(sendData[1])
                else:
                    self.__sendQueue.put(sendData)
            time.sleep(5)
            
    def DoSend(self, data:list[dict]) -> bool:
        try:
            for shard in self.kinesisDetails['Shards']:
                if 'EndingSequenceNumber' not in shard:
                    self.__logger.info(f"Send Kinesis -> Shard:{shard},  Data:{data}")
                    result = self.PutRecords(data, shard)
                    self.__logger.info(f"Send result:{result}")
                    return True
            self.GetShards()
            return False
        except Exception as ex:
            self.__logger.warning("__DoSend, ex: {0} | ".format(ex), exc_info=True)
            return False
        
    def __GetData(self):
        self.__logger.debug("Start Get Lost Packet")
        fileList = sorted(Path(self.__operateInfo.dataFolderPath.lostData).iterdir(),key=os.path.getmtime)
        if len(fileList) != 0:
            for lostData in fileList:
                    readData = self.__ReadFile(lostData)
                    if readData != None:
                        self.__sendQueue.put((readData, self.__operateInfo.dataFolderPath.lostData + lostData.name))
                    else:
                        self.__DeleteData(self.__operateInfo.dataFolderPath.lostData + lostData.name)
        self.__logger.debug("Finish Get Lost Packet")
        
    def __ReadFile(self, lostData:Path) -> list[dict]:
        self.__logger.debug("File Name: {0}".format(lostData.name))
        with open(self.__operateInfo.dataFolderPath.lostData + lostData.name, 'r') as f:
            readData = f.read()
            if len(readData) != 0:
                self.__logger.debug("Get Lost Packet: {0}".format(readData))
                return json.loads(readData)
        return None
                
    def __DeleteData(self, path:str):
        self.__logger.debug("Start Delete File")
        if path != None:
            os.remove(path)
            self.__logger.debug("Remove {0}".format(path))
        self.__logger.debug("Finish Delete File")