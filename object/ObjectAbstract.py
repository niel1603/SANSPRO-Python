from abc import ABC
from dataclasses import dataclass

@dataclass
class Object(ABC):
    index: int