from dataclasses import dataclass


from object._object_abstract import Object
from SANSPRO.object.node import Node

@dataclass
class Offset(Object):
    floor: int
    node: Node
    x: float
    y: float
    z: float