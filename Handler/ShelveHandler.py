import datetime
import os
import shelve


class ShelveHandler():
    def __init__(self, deviceID):
        self.__stringID = str(deviceID)
        self.__tempFilePath = '/home/pi/TempData/TempFile'
        if not os.path.isdir("/home/pi/TempData"):
            os.makedirs("/home/pi/TempData")

    def Read(self):
        result = None
        try:
            tfp = shelve.open(self.__tempFilePath)
            if self.__stringID in tfp:
                result = tfp[self.__stringID]
        finally:
            tfp.close()
            return result
        
    def Write(self, data:dict):
        contain = {}
        dt = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        contain['dt'] = dt
        try:
            tfp = shelve.open(self.__tempFilePath)
            for field, value in data.items():
                contain[field] = value
            tfp[self.__stringID] = contain
        finally:
            tfp.close()