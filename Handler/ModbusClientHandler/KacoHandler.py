from logging import Logger

import crcmod
import serial


class KacoHandler():
    def __init__(self, client:serial.Serial, logger:Logger):
        self.__client = client
        self.__logger = logger
        self.__checkFunction = {"Standard":self.__OneByteChecksum, "Generic":self.__CheckCRC}
    
    def ReadKaco(self, checkCode:str, address:int) -> list[str]:
        result = []
        self.__client.flushInput()
        self.__client.write(f'#{address:02d}0\r'.encode())
        rawData = self.__client.read_until(b'')
        rawDataSplit = rawData.split()
        for r in rawDataSplit:
            result.append(str(r)[2:-1])
        if not self.__checkFunction[checkCode](result, rawData, rawDataSplit, address):
            return None
        return result

    def __OneByteChecksum(self, result:list[str], rawData:bytes, rawDataSplit:list[bytes], address:int) -> bool:
        checkByte = int.from_bytes(rawDataSplit[-2],'big')
        self.__logger.debug(f"KacoHandler, CheckByte: {checkByte}")
        calculateChecksum = 0
        count = 0
        for r in rawData[1:]:
            if count < 56:
                calculateChecksum += r
                count += 1
            else: 
                break
        calculateChecksum = calculateChecksum % 256
        self.__logger.debug(f"KacoHandler, Checksum: {calculateChecksum}")
        if checkByte == calculateChecksum:
            return True
        else:
            return False

    def __CheckCRC(self, result:list[str], rawData:bytes, rawDataSplit:list[bytes], address:int) -> bool:
        self.__logger.debug("Received OK")
        resultString = ''.join(result)
        self.__logger.debug("First Recv>" + resultString + "<")
        receiveString = resultString[:len(resultString) - 4]
        receiveCRC = resultString[len(resultString)-4:]
        crc = crcmod.mkCrcFun(0x11021, 0x0000, True, 0xFFFF)
        checkCRC = str(hex(crc(receiveString.encode())))[2:].zfill(4).upper()
        if (receiveCRC == checkCRC):
            self.__logger.debug("CRC OK {0} {1}".format(receiveCRC, checkCRC))
        else:
            self.__logger.debug("CRC NG {0} {1}".format(receiveCRC, checkCRC))
            return False
        
        if f"{address:02d}" in rawDataSplit[0]:
            self.__logger.debug(f"READ Macaddress: {address} OK<br>")
            return True
        else:
            self.__logger.debug(f"READ Macaddress: {address} NG<br>")
            return False

    
