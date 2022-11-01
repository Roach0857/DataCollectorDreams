from logging import Logger

from Entity import *
from Handler import WriteHandler
from Interface import *


def WriteFactory(deviceInfo: DeviceInfo, deviceConfig: DeviceConfig, logger: Logger) -> IWrite:
    factor = {"prime":WriteHandler.PrimeHandler}
    try:
        return factor[deviceInfo.connectMode](deviceInfo, deviceConfig, logger)
    except Exception as ex:
        logger.warning(f"WriteFactory, ex: {ex} | ", exc_info=True)
        raise ex