from dataclasses import dataclass, field
from typing import Tuple
from object._object_abstract import Object
from SANSPRO.object.elset import Elset
from SANSPRO.object.node import Node

@dataclass
class Slab(Object):
    name: str
    slab_type: int
    elset: Elset
    thick: float
    qDL: float
    qLL: float
    weight: float
    cost: float

@dataclass
class Region(Object):
    floor: int
    slab: Slab
    option: int
    qDL_add: float
    qLL_add: float
    edges: Tuple[Node, Node, Node, Node]
    offset: int
    misc: str = field(repr=False)