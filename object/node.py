from dataclasses import dataclass


from object._object_abstract import Object

@dataclass
class Node(Object):
    x: float
    y: float
    z: float