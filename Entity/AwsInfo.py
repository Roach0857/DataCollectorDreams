from dataclasses import dataclass

@dataclass
class AwsInfo:
    shadowName:str
    endpoint:str
    certificatePath:str
    privateKeyPath:str