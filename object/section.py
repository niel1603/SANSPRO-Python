from dataclasses import dataclass
from abc import ABC
from typing import Tuple

from object._object_abstract import Object

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
class SectionTee(SectionBase):
    width: float #b
    height: float #ht
    thick_web: float #tw
    thick_flange: float #tf

@dataclass
class SectionCircle(SectionBase):
    diameter: float #D

@dataclass
class SectionUser(SectionBase):
    steel_sect: str
    strong_axis: bool