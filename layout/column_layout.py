# column_layout.py

from dataclasses import dataclass
from typing import List

from SANSPRO.model.model import Model
from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.object.node import Node
from SANSPRO.object.column import Column
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.columns import Columns, ColumnsParse, ColumnsEngine, ColumnsAdapter

from SANSPRO.layout._layout_abstract import (
    LayoutBase, 
    LayoutsBase, 
    LayoutParser, 
    LayoutEngine, 
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
    
class ColumnLayoutsEngine(LayoutEngine[Column, ColumnLayout, ColumnLayouts]):

    @staticmethod
    def _normalize_column_nodes_by_coords(
        columns: list[Column],
        nodes: Nodes,
        tol: float = 1e-6,
    ) -> None:
        """
        Rebind Column.location to canonical Node objects by matching (x,y,z).
        Logs warnings but never interrupts the pipeline.
        """

        # Pre-index all nodes by rounded coordinates
        lookup = {
            (round(n.x, 6), round(n.y, 6), round(n.z, 6)): n
            for n in nodes.objects
        }

        for col in columns:
            loc = col.location

            if loc is None:
                print(f"[COL NORMALIZE][WARN] #{col.index}: location=None")
                continue

            key = (round(loc.x, 6), round(loc.y, 6), round(loc.z, 6))
            match = lookup.get(key)

            if match:
                col.location = match
            else:
                print(f"[COL NORMALIZE][WARN] #{col.index}: no node at {key}")



    # ============================================================
    # PUBLIC API — REPLICATE
    # ============================================================
    @staticmethod
    def replicate(
        base_layouts: ColumnLayouts,
        layouts_to_copy: ColumnLayouts,
        *,
        nodes: Nodes,
        nx: int = 0, ny: int = 0, nz: int = 0,
        dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
        include_original: bool = True
    ) -> ColumnLayouts:

        return ColumnLayoutsEngine.apply(
            base_layouts=base_layouts,
            layouts_to_modify=layouts_to_copy,
            include_original=include_original,
            mode="replicate",
            nodes=nodes,
            nx=nx, ny=ny, nz=nz,
            dx=dx, dy=dy, dz=dz,
        )

    # ============================================================
    # PUBLIC API — MIRROR
    # ============================================================
    @staticmethod
    def mirror(
        base_layouts: ColumnLayouts,
        layouts_to_mirror: ColumnLayouts,
        *,
        nodes: Nodes,
        x1: float, y1: float,
        x2: float, y2: float,
        include_original: bool = True
    ) -> ColumnLayouts:

        return ColumnLayoutsEngine.apply(
            base_layouts=base_layouts,
            layouts_to_modify=layouts_to_mirror,
            include_original=include_original,
            mode="mirror",
            nodes=nodes,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
        )

    # ============================================================
    # INTERNAL DISPATCH (must match LayoutEngine)
    # ============================================================
    @classmethod
    def _dispatch_transform(
        cls,
        *,
        items: list[Column],
        target_layout: ColumnLayout,
        include_original: bool,
        mode: str,
        nodes: Nodes,
        op_kwargs: dict,
    ) -> list[Column]:

        if mode == "mirror":
            return cls._transform_items_mirror(
                items=items,
                include_original=include_original,
                target_layout=target_layout,
                nodes=nodes,
                x1=op_kwargs["x1"],
                y1=op_kwargs["y1"],
                x2=op_kwargs["x2"],
                y2=op_kwargs["y2"],
            )

        elif mode == "replicate":
            return cls._transform_items_replicate(
                items=items,
                include_original=include_original,
                target_layout=target_layout,
                nodes=nodes,
                nx=op_kwargs["nx"],
                ny=op_kwargs["ny"],
                nz=op_kwargs["nz"],
                dx=op_kwargs["dx"],
                dy=op_kwargs["dy"],
                dz=op_kwargs["dz"],
            )

        else:
            raise ValueError(f"Unknown mode: {mode}")

    # ============================================================
    # MIRROR
    # ============================================================
    @staticmethod
    def _transform_items_mirror(
        *,
        items: list[Column],
        include_original: bool,
        target_layout: ColumnLayout,
        nodes: Nodes,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> list[Column]:

        base = Columns(objects=items)

        cols_after = ColumnsEngine.mirror(
            columns=base,
            nodes=nodes,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
            include_original=include_original,
        )

        target_layout.items = []
        return cols_after.objects

    # ============================================================
    # REPLICATE
    # ============================================================

    @staticmethod
    def _transform_items_replicate(
        *,
        items: list[Column],
        include_original: bool,
        target_layout: ColumnLayout,
        nodes: Nodes,
        nx: int,
        ny: int,
        nz: int,
        dx: float,
        dy: float,
        dz: float,
    ) -> list[Column]:

        # 1) normalize locations first
        ColumnLayoutsEngine._normalize_column_nodes_by_coords(items, nodes)

        base = Columns(objects=items)

        # 2) replicate — new columns only
        new_cols = ColumnsEngine.replicate(
            columns=base,
            nodes=nodes,
            existing_columns=target_layout.items,
            nx=nx, ny=ny, nz=nz,
            dx=dx, dy=dy, dz=dz,
            include_original=include_original,
        )

        # 3) combine originals + new copies
        if include_original:
            result_items = list(target_layout.items) + list(items) + list(new_cols.objects)
        else:
            result_items = list(target_layout.items) + list(new_cols.objects)

        # DO NOT CLEAR target_layout.items HERE
        return result_items
    
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