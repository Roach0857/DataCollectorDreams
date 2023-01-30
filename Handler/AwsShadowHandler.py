from itertools import groupby
import json
import sys
from logging import Logger
from awsiot.greengrasscoreipc import GreengrassCoreIPCClient
from awsiot.greengrasscoreipc.model import UpdateThingShadowRequest
from Entity.ParseData import ParseData

from Entity.AwsInfo import AwsInfo
from Entity.NodeInfo import NodeInfo
from Entity.ObjectInfo import DeviceInfo

class AwsShadowHandler():
    def __init__(self, awsInfo:AwsInfo, deviceInfoList:list[DeviceInfo], nodeInfo: NodeInfo, ipcClient:GreengrassCoreIPCClient, logger:Logger):
        self.__awsInfo = awsInfo
        self.__deviceInfoList = deviceInfoList
        self.__nodeInfo = nodeInfo
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

    def GetShadowRequest(self, deviceData:ParseData) -> dict:
        totalShadow = dict(map(lambda x:(x.deviceID, {"state":False}), self.__deviceInfoList))
        getDevice = list(filter(lambda x:len(x) != 0, deviceData.data))
        deviceShadow = dict(map(lambda x:(x['deviceID'], {"state":True}), getDevice))
        sortedErr = sorted(deviceData.err, key=lambda x:x['deviceID'])
        groupbyErr = groupby(sortedErr, key=lambda x:x['deviceID'])
        errShadow = {}
        for deviceID, errList in groupbyErr:
            err = {}
            err['eventCode'] = {
                err['address']:err['errCode']
                for err in list(errList)
                }
            errShadow[deviceID] = err
        clientDevice = {}
        clientDevice.update(totalShadow)
        clientDevice.update(deviceShadow)
        clientDevice.update(errShadow)
        return {self.__awsInfo.shadowName:{
            "reported": {
                "nodeID": self.__nodeInfo.node.id,
                "state": True,
                "clientDevice": clientDevice,
                "thingName": sys.argv[1]
                }
            }}