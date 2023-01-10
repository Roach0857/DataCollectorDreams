from dataclasses import dataclass, field


@dataclass
class ParseData:
    data:list[dict] = field(default_factory=lambda: [])
    err:list[dict] = field(default_factory=lambda: [])