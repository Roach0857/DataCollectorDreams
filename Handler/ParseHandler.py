from logging import Logger
from Entity.DeviceConfig import DeviceConfig, Parse
from Entity.ObjectInfo import DeviceInfo
import struct
import Entity
import Handler

class ParseHandler(Handler.CalculateHandler):
    def __init__(self, deviceInfo: DeviceInfo, deviceConfig:DeviceConfig, logger: Logger):
        super().__init__(deviceInfo, logger)
        self.__deviceInfo = deviceInfo
        self.__logger = logger
        self.dataConfig = deviceConfig.data[deviceInfo.type][deviceInfo.modelName]
        self.__parseCode = self.__GetParseCode()
        self.__parseFunstion = {"basic":self.__BasicParse, "sunspec":self.__SunspecParse, "temp":self.__TempParse, "irr":self.__IrrParse, "dm":self.__DmParse}
        self.__dWordFlag = True
        
    def ParseModbus(self, modbusResult:list) -> Entity.ParseData:
        data = {}
        err = {}
        if len(modbusResult) != 0:
            for parseConfig in self.dataConfig.parse:
                if modbusResult[parseConfig.startSite] != None:
                    if 'err' in parseConfig.field:
                        err[parseConfig.field] = self.__parseFunstion[self.__parseCode](modbusResult, parseConfig)
                    else:
                        data[parseConfig.field] = self.__parseFunstion[self.__parseCode](modbusResult, parseConfig)
        if len(data) == 0:
            return Entity.ParseData(False, data, err)
        else:
            return Entity.ParseData(True, data, err)
        
    def __BasicParse(self, modbusResult:list, parseConfig:Parse):
        value = 0
        if parseConfig.length == 2:
            if self.__dWordFlag:
                highWord = modbusResult[parseConfig.startSite]
                lowWord = modbusResult[parseConfig.startSite + 1]
            else:
                highWord = modbusResult[parseConfig.startSite + 1]
                lowWord = modbusResult[parseConfig.startSite]
            if  highWord > 0 :
                value = (highWord * 65536) + lowWord
            else:
                value = lowWord
        else:
            value = modbusResult[parseConfig.startSite]
        if parseConfig.field[:3] == "err":
            return self.__ParseDeviceCode(value)
        else:
            return self.__ParseDeviceValue(value, parseConfig.rate)
    
    def __TempParse(self, modbusResult:list, parseConfig:Parse):
        value = modbusResult[parseConfig.startSite]
        resultString, flag = self.__ConvertToBin(value, True)
        if not flag:
            value = 0 - (int(resultString, 2) + 1)
        return self.__ParseDeviceValue(value, parseConfig.rate)
    
    def __IrrParse(self, modbusResult:list, parseConfig:Parse):
        value = modbusResult[parseConfig.startSite]
        if (value > 32768):
            value = value - 65536
        else:
            value = value
        return self.__ParseDeviceValue(value, parseConfig.rate)
    
    def __DmParse(self, modbusResult:list, parseConfig:Parse):
        value = 0.0
        dataString = ''
        try:   
            for count in range(parseConfig.length):
                dataString = ('{:04x}'.format(modbusResult[parseConfig.startSite + count]) + dataString)
            value = round(struct.unpack('!f', bytes.fromhex(dataString))[0],4)
        except Exception as ex:
            print("DmParse, ex: {0} | ".format(ex), exc_info=True)
        return self.__ParseDeviceValue(value, parseConfig.rate)
    
    def __SunspecParse(self, modbusResult:list, parseConfig:Parse):
        value = modbusResult[parseConfig.startSite]
        valueString = ''
        if parseConfig.field[-2:] == "SF":
            valueString, flag = self.__ConvertToBin(value, True)
        else:
            if parseConfig.length == 2:
                resultStringHigh, flag = self.__ConvertToBin(value) 
                resultStringLow, flag = self.__ConvertToBin(value) 
                valueString = resultStringHigh + resultStringLow
            else:
                valueString, flag = self.__ConvertToBin(value)
        if flag:
            value = int(valueString, base = 2)
        else:
            value = 0 - (int(valueString, base = 2) + 1)
        return self.__ParseDeviceValue(value, parseConfig.rate)
    
    def __ConvertToBin(self, value, complementFlag = False):
        result = ''
        binString = bin(int(value))[2:].zfill(16)
        if complementFlag:
            if binString[0] == '1':
                for binChar in binString[1:]:
                    if binChar == '1':
                        result += '0'
                    else:
                        result += '1'
                return result, False
        return binString, True
    
    def __GetParseCode(self) -> str:
        if self.__deviceInfo.modelName == 'delta':
            self.__dWordFlag = False
            return "basic"
        elif self.__deviceInfo.modelName in ('fronius', 'solaredge'):
            return "sunspec"
        elif self.__deviceInfo.modelName in ('spm-3', 'spm-8'):
            return "dm"
        elif self.__deviceInfo.modelName in ('ctec-03', 'SP-422'):
            return "irr"  
        elif self.__deviceInfo.modelName in ('ctec-04', 'JXBS-3001-TH', 'SD200'):
            return "temp"
        else:
            return "basic"
        
        
    def __ParseDeviceCode(self, value) -> str:
        if type(value) is str:
            return hex(int(value))[2:].zfill(4)
        else:
            return hex(value)[2:].zfill(4)
    
    def __ParseDeviceValue(self, value, rate) -> float:
        if type(value) is str :
            return float(value) / rate
        else:
            return value / rate
