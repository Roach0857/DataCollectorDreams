from logging import Logger
from Entity.ObjectInfo import DeviceInfo
import Interface
import Handler

def ModbusClientFactory(deviceInfo:DeviceInfo, logger:Logger) -> Interface.IModbusClient:
    factory = {"rtu":Handler.RTUHandler, "serial":Handler.SerialHandler}
    try:
        if 'kaco' in deviceInfo.modelName:
            return factory['serial'](deviceInfo, logger)
        else:
            return factory['rtu'](deviceInfo, logger)
    except Exception as ex:
        logger.warning(f"ModbusFactory, ex: {ex} | ", exc_info=True)
        raise ex