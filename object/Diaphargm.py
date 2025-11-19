from typing import List

from dataclasses import dataclass, field

from SANSPRO.object.ObjectAbstract import Object

@dataclass
class Diaphragm(Object):
    tower_data : str
    diaph_data : str
