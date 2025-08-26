from typing import ClassVar, Dict
from dataclasses import dataclass

from variable.VariableAbstract import Variable, VariableParse, VariableAdapter

@dataclass
class Building(Variable):
    layout_node: int
    height_offset: int
    storey: int
    column_layout: int
    beam_layout: int
    wall_layout: int
    slab_data: int
    slab_region: int
    beam_load: int

    key_map: ClassVar[Dict[str, str]] = {
    "layout_node": "Number of Layout Node",
    "height_offset": "Number of Height Offset",
    "storey": "Number of Storey/Floor",
    "column_layout": "Number of Column Layout",
    "beam_layout": "Number of Beam   Layout",
    "wall_layout": "Number of Wall   Layout",
    "slab_data": "Number of Slab Data",
    "slab_region": "Number of Slab Region",
    "beam_load": "Number of Beam Load",
    }

class BuildingParse(VariableParse[Building]):
    block_key = "BUILDING"
    target_cls = Building


class BuildingAdapter(VariableAdapter[Building]):

    @staticmethod
    def format_line(label: str, value: int) -> str:
        return f"  {label:<24}= {value}"

    block_key = "BUILDING"
    target_cls = Building
