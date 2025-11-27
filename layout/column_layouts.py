from typing import Optional, Type, Dict

from SANSPRO.model.model import Model
from SANSPRO.object.column import Column, ColumnLayout
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets

from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.collection.columns import Columns, ColumnsParse, ColumnsAdapter

from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

class ColumnLayouts(Collection[ColumnLayout]):
    header = "LAYCOL"

class ColumnLayoutsParse(CollectionParser[Model, ColumnLayout, ColumnLayouts]):
    """Parser for *LAYCOL* blocks (multi-layout)."""

    @classmethod
    def get_collection(cls) -> Type[ColumnLayouts]:
        return ColumnLayouts

    @classmethod
    def from_model(cls, model: Model, nodes: Nodes, elsets: Elsets) -> ColumnLayouts:
        """Parse multi-layout *LAYCOL* block."""
        block = model.blocks.get(cls.get_collection().header)
        if block is None:
            raise ValueError("Model missing 'LAYCOL' block")

        lines = block.body
        layouts: list[ColumnLayout] = []

        ColumnsParse._col_counter = 0  # reset shared counter

        current_layout: Optional[ColumnLayout] = None
        current_columns: list[Column] = []

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            # Detect layout header
            if stripped.startswith(Columns.header):
                # finalize previous layout
                if current_layout is not None:
                    current_layout.columns = current_columns
                    layouts.append(current_layout)
                    current_columns = []

                # parse layout header
                parts = stripped.split(",")
                layout_no = int(parts[0].split("#")[1])
                total_columns = int(parts[1].split("=")[1])
                current_layout = ColumnLayout(
                    index=layout_no,
                    total_columns=total_columns,
                    columns=[],
                )

            # Parse column line
            elif stripped[0].isdigit():
                column = ColumnsParse.parse_line([raw_line], nodes=nodes, elsets=elsets)
                current_columns.append(column)

        # finalize last layout
        if current_layout is not None:
            current_layout.columns = current_columns
            layouts.append(current_layout)

        return ColumnLayouts(layouts)
    
    @staticmethod
    def remap_elsets(column_layouts: ColumnLayouts,
                     reorder_map: Dict[int, int],
                     new_elsets: Elsets):

        for layout in column_layouts.objects:
            for col in layout.columns:
                old_idx = col.elset.index

                if old_idx not in reorder_map:
                    raise KeyError(
                        f"[ColumnLayoutsParse.remap_elsets] "
                        f"Missing map for old elset {old_idx}"
                    )

                new_idx = reorder_map[old_idx]
                new_elset = new_elsets.get(new_idx)

                if new_elset is None:
                    raise KeyError(
                        f"[ColumnLayoutsParse.remap_elsets] "
                        f"Mapped elset {new_idx} not found in merged_elsets"
                    )

                col.elset = new_elset

class ColumnLayoutsAdapter(ObjectCollectionAdapter[Model, ColumnLayout, ColumnLayouts]):

    @classmethod
    def update_var(cls, layouts: ColumnLayouts, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.beam_layout = len(layouts.objects)
        model = BuildingAdapter.to_model(building, model)

        return model

    @classmethod
    def format_line(cls, layout: ColumnLayout) -> str:

        header = f'  COLUMN LAYOUT #{layout.index}, Total Column = {layout.total_columns}'
        lines = [header]

        # Append each beam line
        for column in layout.columns:
            bline = ColumnsAdapter.format_line(column)
            lines.append(bline)

        lines = "\n".join(lines)
        return lines 