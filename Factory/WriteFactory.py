from logging import Logger
import Entity
import Handler
from Entity.ObjectInfo import DeviceInfo

def WriteFactory(deviceInfo: DeviceInfo, deviceConfig: Entity.DeviceConfig, logger: Logger):
    factor = {"prime":Handler.PrimeHandler}
    try:
        return factor[deviceInfo.modelName](deviceInfo, deviceConfig, logger)
    except Exception as ex:
        logger.warning(f"WriteFactory, ex: {ex} | ", exc_info=True)
        raise ex