from typing import List

from dataclasses import dataclass, field

from object._object_abstract import Object

@dataclass
class Diaphragm(Object):
    tower_data : str
    diaph_data : str
