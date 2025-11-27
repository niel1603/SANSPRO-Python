# column_layout.py

from dataclasses import dataclass

from SANSPRO.model.model import Model
from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.object.column import Column
from SANSPRO.collection.columns import ColumnsParse, ColumnsAdapter

from SANSPRO.layout._layout_abstract import (
    LayoutBase, 
    LayoutsBase, 
    LayoutParser, 
    LayoutAdapter
    )

@dataclass
class ColumnLayout(LayoutBase[Column]):
    """A single FLOOR BEAM LAYOUT block."""
    pass

class ColumnLayouts(LayoutsBase[ColumnLayout]):
    header = "LAYCOL"

class ColumnLayoutsParse(LayoutParser[Model, ColumnLayout, ColumnLayouts, Column]):

    @classmethod
    def get_collection(cls):
        return ColumnLayouts
    
    @classmethod
    def get_item_parser(cls):
        return ColumnsParse

    @classmethod
    def start_of_layout(cls, line: str) -> bool:
        return line.upper().replace(" ", "").startswith("COLUMNLAYOUT")

    @classmethod
    def parse_layout_header(cls, line: str) -> ColumnLayout:
        parts = line.split(",")
        layout_no = int(parts[0].split("#")[1])
        return ColumnLayout(
            index=layout_no,
        )

    @classmethod
    def parse_item(cls, line: str, nodes, elsets) -> Column:
        return ColumnsParse.parse_line([line], nodes=nodes, elsets=elsets)
    
class ColumnLayoutsAdapter(LayoutAdapter[Model, Column, ColumnLayout, ColumnLayouts]):

    @classmethod
    def update_var(cls, layouts: ColumnLayouts, model: Model) -> Model:
        """
        Update BUILDING block variable:
            COLUMN LAYOUT count
        """
        building = BuildingParse.from_mdl(model)
        building.column_layout = len(layouts.layouts)
        return BuildingAdapter.to_model(building, model)

    @classmethod
    def format_layout_header(cls, layout: ColumnLayout) -> str:
        total = len(layout.items)
        return f"  COLUMN LAYOUT #{layout.index}, Total Column = {total}"

    @classmethod
    def format_item(cls, item: Column) -> str:
        return ColumnsAdapter.format_line(item)