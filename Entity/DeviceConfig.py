from dataclasses import dataclass

@dataclass
class Parse:
    field: str
    startSite: int
    length: int
    rate: float

@dataclass
class Read:
    startBit: int
    length: int

class DataConfig:
    def __init__(self, read:list[dict], parse:list[dict], write:dict):
        self.read = [Read(**r) for r in read]
        self.parse = [Parse(**p) for p in parse]
        self.write = {wK:Read(**wV) for wK, wV in write.items()}

@dataclass
class ObjectConfig:
    id: str
    flag: str

class splitConfig:
    def __init__(self, dm:dict[str,list] , inv:dict[str,list]):
        self.dm = {sK:[ObjectConfig(**v)for v in sV] for sK, sV in dm.items()}
        self.inv = {iK:[ObjectConfig(**v)for v in iV] for iK, iV in inv.items()}

class DeviceConfig:
    def __init__(self, data:dict[str, dict], TienJi: dict):
        self.data = {dK:{ddK:DataConfig(**ddV)for ddK, ddV in dV.items()} for dK, dV in data.items()}
        self.TienJi = splitConfig(**TienJi)
