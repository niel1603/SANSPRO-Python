from dataclasses import dataclass


from SANSPRO.object.ObjectAbstract import Object

@dataclass
class Node(Object):
    x: float
    y: float
    z: float