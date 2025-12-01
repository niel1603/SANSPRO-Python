# beam_layout.py

from dataclasses import dataclass
from typing import List, Optional, Tuple, Any

from SANSPRO.model.model import Model
from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.object.beam import Beam
from SANSPRO.object.node import Node
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.beams import Beams, BeamsParse, BeamsEngine, BeamsAdapter

from SANSPRO.layout._layout_abstract import (
    LayoutBase, 
    LayoutsBase, 
    LayoutParser,
    LayoutsQuery,
    LayoutEngine, 
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

class BeamLayoutsEngine(LayoutEngine[Beam, BeamLayout, BeamLayouts]):

    # -----------------------------
    # PUBLIC API: REPLICATE
    # -----------------------------
    @staticmethod
    def replicate(
        base_layouts: BeamLayouts,
        layouts_to_copy: BeamLayouts,
        *,
        nodes: Nodes,
        nx: int = 0, ny: int = 0, nz: int = 0,
        dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
        include_original: bool = True,
    ) -> BeamLayouts:
        return BeamLayoutsEngine.apply(
            base_layouts=base_layouts,
            layouts_to_modify=layouts_to_copy,
            include_original=include_original,
            mode="replicate",
            nodes=nodes,
            nx=nx, ny=ny, nz=nz,
            dx=dx, dy=dy, dz=dz,
        )

    # -----------------------------
    # PUBLIC API: MIRROR (unchanged)
    # -----------------------------
    @classmethod
    def mirror(
        cls,
        base_layouts: BeamLayouts,
        layouts_to_mirror: BeamLayouts,
        *,
        nodes: Nodes,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        include_original: bool = True,
    ) -> BeamLayouts:
        return cls.apply(
            base_layouts=base_layouts,
            layouts_to_modify=layouts_to_mirror,
            include_original=include_original,
            mode="mirror",
            nodes=nodes,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
        )

    # -----------------------------
    # NODE NORMALIZATION (by coords)
    # -----------------------------
    @staticmethod
    def _normalize_beam_nodes_by_coords(
        beams: list[Beam],
        nodes: Nodes,
        tol: float = 1e-6,
    ) -> None:
        """
        Rebind Beam.start / Beam.end to the canonical Node objects
        from `nodes` using coordinates as key.

        Logs warnings but keeps going if some nodes are missing.
        """

        lookup: dict[tuple[float, float, float], Node] = {}
        for n in nodes.objects:
            key = (round(n.x, 6), round(n.y, 6), round(n.z, 6))
            lookup[key] = n

        for b in beams:
            s = b.start
            e = b.end
            missing = False

            # start
            if s is not None:
                key_s = (round(s.x, 6), round(s.y, 6), round(s.z, 6))
                ns = lookup.get(key_s)
                if ns is not None:
                    b.start = ns
                else:
                    print(f"[normalize][WARN] Beam#{b.index}: missing START node at {key_s}")
                    missing = True

            # end
            if e is not None:
                key_e = (round(e.x, 6), round(e.y, 6), round(e.z, 6))
                ne = lookup.get(key_e)
                if ne is not None:
                    b.end = ne
                else:
                    print(f"[normalize][WARN] Beam#{b.index}: missing END node at {key_e}")
                    missing = True

            if missing:
                # We keep the beam but with original node objects.
                # This is intentional: we don't crash, but downstream
                # replication may skip it if matching nodes don't exist.
                pass

    # -----------------------------
    # INTERNAL DISPATCH
    # -----------------------------
    @classmethod
    def _dispatch_transform(
        cls,
        *,
        items: list[Beam],
        target_layout: BeamLayout,
        include_original: bool,
        mode: str,
        nodes: Nodes,
        op_kwargs: dict,
    ) -> list[Beam]:

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

    # -----------------------------
    # MIRROR OP (unchanged logic)
    # -----------------------------
    @staticmethod
    def _transform_items_mirror(
        *,
        items: list[Beam],
        include_original: bool,
        target_layout: BeamLayout,
        nodes: Nodes,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> list[Beam]:

        base = Beams(objects=items)

        beams_after = BeamsEngine.mirror(
            beams=base,
            nodes=nodes,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
            include_original=include_original,
        )

        # For mirror we overwrite the target layout’s items directly
        target_layout.items = beams_after.objects
        return target_layout.items

    # -----------------------------
    # REPLICATE OP
    # -----------------------------
    @staticmethod
    def _transform_items_replicate(
        *,
        items: list[Beam],
        include_original: bool,
        target_layout: BeamLayout,
        nodes: Nodes,
        nx: int,
        ny: int,
        nz: int,
        dx: float,
        dy: float,
        dz: float,
    ) -> list[Beam]:

        # 1) First normalize source beams to canonical node objects.
        #    This fixes any “wrong node instance / right coords” problems.
        BeamLayoutsEngine._normalize_beam_nodes_by_coords(items, nodes)

        base = Beams(objects=items)

        # 2) Replicate against existing beams already in the target layout
        new_beams = BeamsEngine.replicate(
            beams=base,
            nodes=nodes,
            existing_beams=target_layout.items,
            nx=nx, ny=ny, nz=nz,
            dx=dx, dy=dy, dz=dz,
            include_original=include_original,
        )

        # 3) Merge according to include_original
        if include_original:
            result_items = list(target_layout.items) + new_beams.objects
        else:
            result_items = new_beams.objects

        # Let LayoutEngine.apply() reindex later
        return result_items

class BeamLayoutsQuery(LayoutsQuery[Beam, BeamLayout, BeamLayouts]):

    TOL = 1e-6

    @staticmethod
    def find_beam_by_xyz(
        layouts: BeamLayouts,
        floor: int,
        sx: float, sy: float, sz: float,
        ex: float, ey: float, ez: float,
        tol: float = 1e-6,
    ) -> Beam | None:

        def close(a, b): 
            return abs(a - b) <= tol

        for b in layouts.get(floor).items:
            s, e = b.start, b.end

            # direct match
            if (close(s.x, sx) and close(s.y, sy) and close(s.z, sz) and
                close(e.x, ex) and close(e.y, ey) and close(e.z, ez)):
                return b

            # reversed match
            if (close(s.x, ex) and close(s.y, ey) and close(s.z, ez) and
                close(e.x, sx) and close(e.y, sy) and close(e.z, sz)):
                return b

        return None

    @staticmethod
    def get_beam_by_id(layouts: BeamLayouts, beam_id: int) -> tuple[Optional[Beam], Optional[BeamLayout]]:
        """
        Find a beam by its global index across all layouts.
        """
        for layout in layouts.layouts:
            beam = layout.get_item(beam_id)
            if beam is not None:
                return beam, layout
        return None, None

    @classmethod
    def beam_geom_key(cls, n1: Node, n2: Node):
        p1 = (round(n1.x,6), round(n1.y,6), round(n1.z,6))
        p2 = (round(n2.x,6), round(n2.y,6), round(n2.z,6))
        return tuple(sorted((p1, p2)))

    @classmethod
    def find_beam_by_nodes_in_floor(
        cls,
        layouts: BeamLayouts,
        floor: int,
        n1: Node,
        n2: Node,
    ) -> tuple[Beam | None, BeamLayout | None]:
        """
        Find a beam on a given floor whose start/end nodes match (n1, n2)
        geometrically, ignoring direction (start/end order).
        """

        layout = layouts.get(floor)
        if not layout:
            return None, None

        target_key = cls.beam_geom_key(n1, n2)

        for beam in layout.items:
            if beam.start is None or beam.end is None:
                continue

            beam_key = cls.beam_geom_key(beam.start, beam.end)

            if beam_key == target_key:
                return beam, layout

        return None, layout


    @staticmethod
    def match_beam_by_nodes(layouts: BeamLayouts, n1: Node, n2: Node):
        # geometric search using two-node matcher
        return LayoutsQuery.find_item_by_nodes(layouts, n1, n2)

    # ------------------------------------------------------------
    # Layout-level
    # ------------------------------------------------------------
    @staticmethod
    def get_layout(layouts: BeamLayouts, index: int) -> Optional[BeamLayout]:
        return layouts._by_index.get(index)

    @staticmethod
    def layouts_by_indices(layouts: BeamLayouts, indices: List[int]) -> BeamLayouts:
        selected = [lay for lay in layouts.layouts if lay.index in indices]
        return BeamLayouts(selected)

    # ------------------------------------------------------------
    # Iterate utilities
    # ------------------------------------------------------------
    @staticmethod
    def iter_items(layouts: BeamLayouts):
        for lay in layouts.layouts:
            for item in lay.items:
                yield item, lay

    @staticmethod
    def flatten_items(layouts: BeamLayouts) -> List[Beam]:
        return [b for b, _ in BeamLayoutsQuery.iter_items(layouts)]

    # ------------------------------------------------------------
    # Item by index across all layouts
    # ------------------------------------------------------------
    @staticmethod
    def get_item(layouts: BeamLayouts, item_index: int) -> Tuple[Optional[Beam], Optional[BeamLayout]]:
        for lay in layouts.layouts:
            b = lay.get_item(item_index)
            if b:
                return b, lay
        return None, None

    # ------------------------------------------------------------
    # Geometry matching
    # ------------------------------------------------------------
    @staticmethod
    def _match_nodes(a: Node, b: Node, tol: float) -> bool:
        return (
            abs(a.x - b.x) < tol and
            abs(a.y - b.y) < tol and
            abs(a.z - b.z) < tol
        )

    @classmethod
    def find_by_nodes(cls, layouts: BeamLayouts,
                       n1: Node, n2: Node) -> Tuple[Optional[Beam], Optional[BeamLayout]]:
        tol = cls.TOL

        for b, lay in cls.iter_items(layouts):
            if ((cls._match_nodes(b.start, n1, tol) and cls._match_nodes(b.end, n2, tol)) or
                (cls._match_nodes(b.start, n2, tol) and cls._match_nodes(b.end, n1, tol))):
                return b, lay

        return None, None

    # ------------------------------------------------------------
    # Filter items by floor
    # ------------------------------------------------------------
    @staticmethod
    def items_by_floor(layouts: BeamLayouts, floor: int) -> List[Beam]:
        return [b for b, _ in BeamLayoutsQuery.iter_items(layouts) if b.floor == floor]

    # ------------------------------------------------------------
    # Find the "replicated/mirrored" equivalent beam
    # ------------------------------------------------------------
    @classmethod
    def find_equivalent(cls,
                        layouts: BeamLayouts,
                        target_beam: Beam) -> Tuple[Optional[Beam], Optional[BeamLayout]]:
        """Find the beam in layouts with same geometric endpoints as target."""
        return cls.find_by_nodes(layouts, target_beam.start, target_beam.end)


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
