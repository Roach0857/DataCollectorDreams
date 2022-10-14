from dataclasses import dataclass


@dataclass
class DeadbandSet:
    acCurrentL1:float = None
    acCurrentL2:float = None
    acCurrentL3:float = None
    acCurrentLN:float = None
    acVoltageL12:float = None
    acVoltageL21:float = None
    acVoltageL31:float = None
    acActivePower:float = None
    acReactivePower:float = None
    powerFactor:float = None
    frequency:float = None