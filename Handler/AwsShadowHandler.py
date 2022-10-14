import json
import sys
from logging import Logger

from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from awsiot.greengrasscoreipc.model import UpdateThingShadowRequest

import Entity


class AwsShadowHandler():
    def __init__(self, awsInfo:Entity.AwsInfo, nodeInfo: Entity.NodeInfo, ipcClient:GreengrassCoreIPCClient, logger:Logger):
        self.__nodeInfo = nodeInfo
        self.__awsInfo = awsInfo
        self.__logger = logger
        self.__timeout = 10
        self.__ipcClient = ipcClient
        
    def UpdateShadow(self, shadow:dict) -> bytes:
        try:
            request = UpdateThingShadowRequest()
            request.thing_name = sys.argv[1]
            request.shadow_name = self.__awsInfo.shadowName
            request.payload = bytes(json.dumps(shadow), "utf-8")
            clientReault = self.__ipcClient.new_update_thing_shadow()
            clientReault.activate(request)
            clientResponse = clientReault.get_response()
            result = clientResponse.result(self.__timeout)
            self.__logger.info("Update Shadow {0}".format(result.payload))
            return result.payload
        except Exception as ex:
            self.__logger.warning("Shadow Update, ex: {0} | ".format(ex), exc_info=True)
            raise ex
        
    def GetShadowRequest(self, readResult:list[Entity.ParseData]) -> dict:
        clientDevice = {}
        for readData in readResult:
            strDeviceID = str(readData.data['deviceID'])
            clientDevice[strDeviceID] = readData.flag
        return {self.__awsInfo.shadowName:{
            "reported": {
                "nodeID": self.__nodeInfo.node.id,
                "state": True,
                "clientDevice": clientDevice,
                "thingName": sys.argv[1]
                }
            }}