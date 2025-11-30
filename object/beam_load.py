from enum import IntEnum
from dataclasses import dataclass
from typing import Tuple
from object._object_abstract import Object
from SANSPRO.object.beam import Beam

class LoadDirectionType(IntEnum):
    QX = 4
    QY = 5
    QZ = 6
    QY_GLOBAL = 15

@dataclass
class FrameLoadTable(Object):
    load_type: LoadDirectionType
    q: float
    s1: float
    s2: float
    misc: Tuple[int, int]
    note: str

@dataclass
class BeamLoad(Object):
    load_case: int
    floor: int
    beam_id: int
    load: FrameLoadTable