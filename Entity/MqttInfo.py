from dataclasses import dataclass


@dataclass
class MqttInfo:
    host:str
    port:str
    user:str
    password:str