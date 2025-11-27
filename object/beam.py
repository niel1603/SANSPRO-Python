from typing import List
from dataclasses import dataclass, field

from object._object_abstract import Object
from SANSPRO.object.elset import Elset
from SANSPRO.object.node import Node


@dataclass
class Beam(Object):
    start: Node
    end: Node
    elset: Elset
    group: int
    beam_type: int
    misc: str = field(repr=False)


@dataclass
class BeamLayout:
    index: int
    total_beams: int
    beams: List[Beam]