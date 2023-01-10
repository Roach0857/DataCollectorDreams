from logging import Logger
from Entity.DeviceConfig import DeviceConfig
from Entity.ObjectInfo import DeviceInfo
from Handler.WriteHandler.PrimeHandler import PrimeHandler
from Interface.IWrite import IWrite


def WriteFactory(deviceInfo: DeviceInfo, deviceConfig: DeviceConfig, logger: Logger) -> IWrite:
    factor = {"prime":PrimeHandler}
    try:
        return factor[deviceInfo.connectMode](deviceInfo, deviceConfig, logger)
    except Exception as ex:
        logger.warning(f"WriteFactory, ex: {ex} | ", exc_info=True)
        raise ex