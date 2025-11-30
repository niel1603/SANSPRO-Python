from enum import IntEnum, IntFlag
from dataclasses import dataclass, field
from typing import Tuple
from object._object_abstract import Object
from SANSPRO.object.elset import Elset
from SANSPRO.object.node import Node

class SlabSupportOption(IntEnum):
    ONE_WAY = 1
    TWO_WAY = 2
    TWO_WAY_Y = 3
    TWO_WAY_x = 4

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
    option: SlabSupportOption
    qDL_add: float
    qLL_add: float
    edges: Tuple[Node, Node, Node, Node]
    offset: int
    misc: str = field(repr=False)