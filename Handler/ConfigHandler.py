import os
import sys
import time
import json
import boto3
from botocore.exceptions import ClientError


class ConfigHandler():
    def GetInfo(self, path:str) -> dict:
        File = None
        FileData = None
        Result = None
        File = open(path, 'r')
        FileData = File.read()
        File.close()
        Result = json.loads(FileData)
        return Result
    
    def __Check(self) -> bool:
        result = False
        systemType = sys.argv[1].split("-")[1]
        if systemType == "ecu":
            return True
        elif systemType == "debug":
            return False
        else:
            os.popen("systemctl stop ntp.service; echo $?").read()
            while(True):
                count = 1
                ntpServer = ["tock.stdtime.gov.tw",
                            "watch.stdtime.gov.tw",
                            "time.stdtime.gov.tw",
                            "clock.stdtime.gov.tw",
                            "tick.stdtime.gov.tw"]
                ntpResult = None
                ntpResult = os.popen("sudo ntpdate {}".format(ntpServer[count%5])).read()
                print("ntpResult:{}".format(ntpResult))
                if ("offset" in ntpResult):
                    result = True
                    break
                elif (count == 60):
                    break
                time.sleep(5)
                count +=1
            os.popen("systemctl start ntp.service; echo $?").read()
        return result
    
    def GetParameter(self, thingName:str):
        session = boto3.Session()
        credentials = session.get_credentials()
        try:
            if self.__Check():
                result = None
                ssm_client = boto3.client('ssm', 
                                        region_name=session.region_name,
                                        aws_access_key_id=credentials.access_key,
                                        aws_secret_access_key=credentials.secret_key)
                parameterResult = ssm_client.get_parameter(Name=thingName)
                result = json.loads(parameterResult["Parameter"]["Value"])
                if result != None:
                    with open("Config/SystemInfo.json", "w") as file:
                        file.write(json.dumps(result, indent=4))
        except ClientError as ex:
            raise ex
        except Exception as ex:
            raise ex