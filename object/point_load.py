from dataclasses import dataclass

from object._object_abstract import Object

@dataclass
class PointLoad(Object):
    load_case: int
    floor: int
    node_id: int
    fx: float
    fy: float
    fz: float
    mx: float
    my: float
    mz: float
    misc: int = 1 # unknown variable, default value as 1
    blast : int = 0 # known variable, unknown "usefulness", default value as 0