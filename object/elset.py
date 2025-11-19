from dataclasses import dataclass

from abc import ABC
from typing import Tuple
from typing import TypeVar, Type

from SANSPRO.object.ObjectAbstract import Object

from SANSPRO.object.Section import SectionBase
from SANSPRO.object.design import DesignBase
from SANSPRO.object.material import MaterialBase

# old
# @dataclass
# class Elset(Object, ABC):
#     material: int
#     section: int
#     design: int
#     texture: int

@dataclass
class Elset(Object):
    material: MaterialBase
    section: SectionBase
    design: DesignBase
    texture: int