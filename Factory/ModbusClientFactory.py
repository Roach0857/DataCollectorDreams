from logging import Logger

from Entity import *
from Handler.ModbusClientHandler import *
from Interface import *


def ModbusClientFactory(deviceInfo:DeviceInfo, logger:Logger) -> IModbusClient:
    factory = {"rtu":RTUHandler, "serial":SerialHandler}
    try:
        if 'kaco' in deviceInfo.connectMode:
            return factory['serial'](deviceInfo, logger)
        else:
            return factory['rtu'](deviceInfo, logger)
    except Exception as ex:
        logger.warning(f"ModbusFactory, ex: {ex} | ", exc_info=True)
        raise ex