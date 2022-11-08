from dataclasses import dataclass


@dataclass
class InvSet:
    powerFactor:int = None
    acActivePower:int = None
    acReactivePower:int = None
    vpSet:int = None