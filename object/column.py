from typing import List
from dataclasses import dataclass, field

from object._object_abstract import Object
from object.elset import Elset
from object.node import Node


@dataclass
class Column(Object):
    location: Node
    elset: Elset
    group: int
    alpha: int
    misc: str = field(repr=False)

@dataclass
class ColumnLayout(Object):
    index: int
    total_columns: int
    columns: List[Column]