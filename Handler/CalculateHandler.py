import datetime
from logging import Logger

from Entity.ObjectInfo import DeviceInfo
from Handler.ShelveHandler import ShelveHandler

class CalculateHandler():
    def __init__(self, deviceInfo:DeviceInfo, logger:Logger):
        self.__deviceInfo = deviceInfo
        self.__logger = logger
        self.__calculateCode = self.__GetCalculateCode()
        self.__calculateFunction = {"basic":self.__BasicCalculate, 
                                    "getAcCurrentLN":self.__GetAcCurrentLN,
                                    "getAcActivePower":self.__GetAcActivePower, 
                                    "getAcActiveDailyEnergy":self.__GetAcActiveDailyEnergy, 
                                    "getAcActiveEnergy":self.__GetAcActiveEnergy}
        self.__shelveHandler = ShelveHandler(deviceInfo.deviceID)
        self.__scaleFalg = False
        
    def CalculateData(self, parseResult:dict) -> dict:
        if len(parseResult) != 0:
            return self.__calculateFunction[self.__calculateCode](parseResult)
        else:
            return parseResult
    
    def __BasicCalculate(self, parseResult:dict) -> dict:
        return parseResult
    
    def __GetAcCurrentLN(self, parseResult:dict):
        result = dict(map(lambda x:(x[0], x[1]), parseResult.items()))
        c1 = result['acCurrentL1']
        c2 = result['acCurrentL2']
        c3 = result['acCurrentL3']
        result['acCurrentLN'] = ((c1 ** 2) + (c2 ** 2) + (c3 ** 2) - (c1 * c2) - (c2 * c3) - (c3 * c1)) ** 0.5
        return result
        
    def __GetAcActivePower(self, parseResult:dict) -> dict:
        result = {}
        totalPower = 0
        for field, value in parseResult.items():
            result[field] = value
            if field[:13] == "dcActivePower":
                totalPower += value
        if totalPower != 0:
            result["dcActivePower"] = totalPower
        return result
    
    def __GetAcActiveDailyEnergy(self, parseResult:dict) -> dict:
        result:dict
        if self.__scaleFalg:
            result = self.__CalculateScale(parseResult)
        else:
            result = dict(map(lambda x:(x[0], x[1]), parseResult.items()))
        shelveData = self.__shelveHandler.Read()
        if shelveData != None:
            self.__logger.debug(f"{self.__deviceInfo.deviceID}_shelveData | acActiveEnergy:{shelveData['acActiveEnergy']}, acActiveEnergyDaily:{shelveData['acActiveEnergyDaily']}")
            localDataTime = datetime.datetime.strptime(shelveData['dt'], '%Y/%m/%d %H:%M:%S').date()
            if result['acActiveEnergy'] == 0.0:
                result['acActiveEnergy'] = shelveData['acActiveEnergy']
            if (datetime.datetime.now().date() > localDataTime):
                result['acActiveEnergyDaily'] = 0.0
            else:
                result['acActiveEnergyDaily'] = shelveData['dailyEnergy'] + ( result['acActiveEnergy'] - shelveData['totalEnergy'])
        else:
            self.__logger.debug(f"{self.__deviceInfo.deviceID}_shelveData is null")
            result['acActiveEnergyDaily'] = 0.0
        self.__logger.debug(f"{self.__deviceInfo.deviceID}_resultData | acActiveEnergy:{result['acActiveEnergy']}, acActiveEnergyDaily:{result['acActiveEnergyDaily']}")
        writeData = {}
        writeData["acActiveEnergyDaily"] = result["acActiveEnergyDaily"]
        writeData["acActiveEnergy"] = result["acActiveEnergy"]
        self.__shelveHandler.Write(writeData)
        return result
    
    def __GetAcActiveEnergy(self, parseResult:dict) -> dict:
        result = {}
        for field, value in parseResult.items():
            result[field] = value
        shelveData = self.__shelveHandler.Read()
        if shelveData != None:
            self.__logger.debug(f"{self.__deviceInfo.deviceID}_shelveData | acActiveEnergy:{shelveData['acActiveEnergy']}, acActiveEnergyDaily:{shelveData['dailyEnergy']}")
            if shelveData['dailyEnergy'] <= parseResult['acActiveEnergyDaily']:
                energyDeviation = parseResult['acActiveEnergyDaily'] - shelveData['dailyEnergy']
                shelveData['totalEnergy'] += energyDeviation
            else:
                shelveData['totalEnergy'] += parseResult['acActiveEnergyDaily']
            result['acActiveEnergy'] = shelveData['totalEnergy']
        else:
            self.__logger.debug(f"{self.__deviceInfo.deviceID}_shelveData is null")
            result['acActiveEnergy'] = parseResult['acActiveEnergyDaily']
        self.__logger.debug(f"{self.__deviceInfo.deviceID}_resultData | acActiveEnergy:{result['acActiveEnergy']}, acActiveEnergyDaily:{result['acActiveEnergyDaily']}")
        writeData = {}
        writeData["acActiveEnergyDaily"] = result["acActiveEnergyDaily"]
        writeData["acActiveEnergy"] = result["acActiveEnergy"]
        self.__shelveHandler.Write(writeData)
        return result
    
    def __CalculateScale(self, parseResult:dict) -> dict:
        result = {}
        sfField = {}
        valueField = {}
        for field, value in parseResult.items():
            if field[-2:] == 'SF':
                sfField[field[:-2]] = value
            else:
                valueField[field] = value
        for vField, vValue in  valueField.items():
            if vField in sfField:
                result[vField] = vValue * (10 ** sfField[vField])
            else:
                result[vField] = vValue
        
    def __GetCalculateCode(self):
        if self.__deviceInfo.connectMode in ('prime', 'cyberpower'):
            return "getAcActivePower"
        elif self.__deviceInfo.connectMode  == 'fronius':
            return "getAcActiveDailyEnergy"
        elif 'solaredge' in self.__deviceInfo.connectMode:
            self.__scaleFalg = True
            return "getAcActiveDailyEnergy"
        elif 'kaco' in self.__deviceInfo.connectMode:
            return "getAcActiveEnergy"
        elif self.__deviceInfo.connectMode == 'spm-3':
            return "getAcCurrentLN"
        else:
            return "basic"
        
    