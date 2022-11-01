from dataclasses import dataclass


@dataclass
class InvSetCheck:
    powerFactor:bool = False
    acActivePower:bool = False
    acReactivePower:bool = False
    vpSet:bool = False
    smartSwtich:bool = False
