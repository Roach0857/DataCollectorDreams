from dataclasses import dataclass


@dataclass
class DeadbandSet:
    acCurrentL1:float = None
    acCurrentL2:float = None
    acCurrentL3:float = None
    acCurrentLN:float = None
    acLineVoltageL1L2:float = None
    acLineVoltageL2L3:float = None
    acLineVoltageL3L1:float = None
    acActivePower:float = None
    acReactivePower:float = None
    powerFactor:float = None
    frequency:float = None