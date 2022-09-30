from dataclasses import dataclass

@dataclass
class LogInfo:
    fileLevel: str
    consoleLevel: str
    path: str