from dataclasses import dataclass
from abc import ABC
from typing import Tuple

from SANSPRO.object.ObjectAbstract import Object

@dataclass
class MaterialBase(Object, ABC):
    type_index: int
    type_name: str
    name: str
    misc1: Tuple[int, int, int, int]

@dataclass
class MaterialIsotropic(MaterialBase):

    fc1: int
    time_dependent: bool
    alpha: float
    beta: float

    misc2 : int

    thermal_coeficient: float
    unit_weight: float
    elastic_mod: float
    shear_mod: float
    poisson_ratio: float
    
@dataclass
class MaterialSpring(MaterialBase):

    misc2 : int

    spring_stiff: float
    spring_min: float
    spring_max: float