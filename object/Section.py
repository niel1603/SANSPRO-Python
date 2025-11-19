from dataclasses import dataclass
from abc import ABC
from typing import Tuple

from SANSPRO.object.ObjectAbstract import Object

@dataclass
class SectionBase(Object, ABC):
    type_index: int
    type_name: str
    misc: Tuple[int, int, int, int, float, float]
    name: str

@dataclass
class SectionThickness(SectionBase):
    thickness: float

@dataclass
class SectionRect(SectionBase):
    width: float #b and bf
    height: float #ht
    slab_thick: float #tf

@dataclass
class SectionCircle(SectionBase):
    diameter: float #D