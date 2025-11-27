# beam_layout.py

from dataclasses import dataclass
from typing import List

from SANSPRO.model.model import Model
from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.object.beam import Beam
from SANSPRO.collection.beams import BeamsParse, BeamsAdapter

from SANSPRO.layout._layout_abstract import (
    LayoutBase, 
    LayoutsBase, 
    LayoutParser, 
    LayoutAdapter
    )

@dataclass
class BeamLayout(LayoutBase[Beam]):
    """A single FLOOR BEAM LAYOUT block."""
    pass

class BeamLayouts(LayoutsBase[BeamLayout]):
    header = "LAYBEAM"

class BeamLayoutsParse(LayoutParser[Model, BeamLayout, BeamLayouts, Beam]):

    @classmethod
    def get_collection(cls):
        return BeamLayouts
    
    @classmethod
    def get_item_parser(cls):
        return BeamsParse

    @classmethod
    def start_of_layout(cls, line: str) -> bool:
        return line.upper().replace(" ", "").startswith("FLOORBEAMLAYOUT")

    @classmethod
    def parse_layout_header(cls, line: str) -> BeamLayout:
        parts = line.split(",")
        layout_no = int(parts[0].split("#")[1])
        return BeamLayout(
            index=layout_no,
        )

    @classmethod
    def parse_item(cls, line: str, nodes, elsets) -> Beam:
        return BeamsParse.parse_line([line], nodes=nodes, elsets=elsets)

class BeamLayoutsAdapter(LayoutAdapter[Model, Beam, BeamLayout, BeamLayouts]):

    @classmethod
    def update_var(cls, layouts: BeamLayouts, model: Model) -> Model:
        """Update BUILDING: BEAM LAYOUT count."""
        building = BuildingParse.from_mdl(model)
        building.beam_layout = len(layouts.layouts)
        return BuildingAdapter.to_model(building, model)

    @classmethod
    def format_layout_header(cls, layout: BeamLayout) -> str:
        total = len(layout.items)
        return f"  FLOOR BEAM LAYOUT #{layout.index}, Total Beam = {total}"

    @classmethod
    def format_item(cls, item: Beam) -> str:
        return BeamsAdapter.format_line(item) 
