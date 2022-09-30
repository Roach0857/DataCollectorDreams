from logging import Logger
import Entity
from Entity.ObjectInfo import DeviceInfo
import Abstract
import Handler

def ModbusFactory(locationObjectID:str, mode:str, deviceInfo:DeviceInfo, deviceConfig:Entity.DeviceConfig, logger:Logger) -> Abstract.ModbusAbstract:
    factory = {"rtu":Handler.RTUHandler, "serial":Handler.SerialHandler}
    try:
        if deviceInfo.modelID in (8, 9, 12):
            return factory['serial'](locationObjectID, mode, deviceInfo, deviceConfig, logger)
        else:
            return factory['rtu'](locationObjectID, mode, deviceInfo, deviceConfig, logger)
    except Exception as ex:
        logger.warning(f"ModbusFactory, ex: {ex} | ", exc_info=True)
        raise ex