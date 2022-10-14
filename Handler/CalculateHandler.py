import datetime
from logging import Logger

import Handler
from Entity.ObjectInfo import DeviceInfo


class CalculateHandler():
    def __init__(self, deviceInfo:DeviceInfo, logger:Logger):
        self.__deviceInfo = deviceInfo
        self.__logger = logger
        self.__calculateCode = self.__GetCalculateCode()
        self.__calculateFunction = {"basic":self.__BasicCalculate, 
                                  "getAcActivePower":self.__GetAcActivePower, 
                                  "getAcActiveDailyEnergy":self.__GetAcActiveDailyEnergy, 
                                  "getAcActiveEnergy":self.__GetAcActiveEnergy}
        self.__shelveHandler = Handler.ShelveHandler(deviceInfo.deviceID)
        self.__scaleFalg = True
        
    def CalculateData(self, parseResult:dict) -> dict:
        return self.__calculateFunction[self.__calculateCode](parseResult)
    
    def __BasicCalculate(self, parseResult:dict) -> dict:
        return parseResult
    
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
        result = {}
        if self.__scaleFalg:
            result = self.__CalculateScale(parseResult)
        else:
            for field, value in parseResult.items():
                result[field] = value
        shelveData = self.__shelveHandler.Read()
        if shelveData != None:
            self.__logger.debug(f"{self.__deviceInfo.deviceID}_shelveData | acActiveEnergy:{shelveData['acActiveEnergy']}, acActiveEnergyDaily:{shelveData['acActiveEnergyDaily']}")
            localDataTime = datetime.datetime.strptime(shelveData['dt'], '%Y/%m/%d %H:%M:%S').date()
            if result['acActiveEnergy'] == 0.0:
                result['acActiveEnergy'] = shelveData['acActiveEnergy']
            if (datetime.datetime.now().date() > localDataTime):
                result['acActiveEnergyDaily'] = 0.0
            else:
                result['acActiveEnergyDaily'] = shelveData['dailyEnergy'] + ( result['acActiveEnergy'] - shelveData['acActiveEnergy'])
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
            self.__logger.debug(f"{self.__deviceInfo.deviceID}_shelveData | acActiveEnergy:{shelveData['acActiveEnergy']}, acActiveEnergyDaily:{shelveData['acActiveEnergyDaily']}")
            if shelveData['dailyEnergy'] <= parseResult['acActiveEnergyDaily']:
                energyDeviation = parseResult['acActiveEnergyDaily'] - shelveData['acActiveEnergyDaily']
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
        for sfField, sfValue in sfField.items():
            for vField, vValue in  valueField.items():
                if sfField in vField:
                    result[vField] = vValue * (10 ** sfValue)
                else:
                    result[vField] = vValue
        
    def __GetCalculateCode(self):
        if self.__deviceInfo.modelName in ('prime', 'cyberpower'):
            return "getAcActivePower"
        elif self.__deviceInfo.modelName  == 'fronius':
            return "getAcActiveDailyEnergy"
        elif self.__deviceInfo.modelName  == 'solaredge':
            self.__scaleFalg = False
            return "getAcActiveDailyEnergy"
        elif self.__deviceInfo.modelName in ('kaco_1', 'kaco_2', 'kaco_3'):
            return "getAcActiveEnergy"
        else:
            return "basic"
        
    