from dataclasses import dataclass

from Object.ObjectAbstract import Object

@dataclass
class Node(Object):
    x: float
    y: float
    z: float