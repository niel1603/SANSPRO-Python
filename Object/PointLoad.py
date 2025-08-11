from dataclasses import dataclass

from Object.ObjectAbstract import Object
from Object.Node import Node

@dataclass
class PointLoad(Object):
    load_case: int
    floor: int
    node: Node
    fx: float
    fy: float
    fz: float
    mx: float
    my: float
    mz: float
    misc: int = 1 # unknown variable, default value as 1
    blast : int = 0 # known variable, unknown "usefulness", default value as 0