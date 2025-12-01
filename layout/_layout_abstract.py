# _layout_abstract.py

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, List, Optional, Dict, Callable, Tuple

from SANSPRO.model.model import Model, BlockAdapter
from SANSPRO.collection.nodes import Nodes
from object._object_abstract import Object

# ------------------------------------------------------------
# TYPE VARIABLES
# ------------------------------------------------------------

M = TypeVar("M", bound="Model")              # Model type
I = TypeVar("I", bound="Object")             # Layout item type (Beam, SlabRegion, Wall, etc.)
L = TypeVar("L", bound="LayoutBase")         # Layout type (BeamLayout)
C = TypeVar("C", bound="LayoutsBase")        # Layout collection type (BeamLayouts)

# ------------------------------------------------------------
# BASE LAYOUT OBJECT
# ------------------------------------------------------------

@dataclass
class LayoutBase(Generic[I]):
    index: int
    items: List[I] = field(default_factory=list)

    _by_index: Dict[int, I] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        self.rebuild_index()

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        return iter(self.items)

    # --------------------------------------------------------
    # Rebuild internal index dictionary
    # --------------------------------------------------------
    def rebuild_index(self):
        self._by_index.clear()
        for item in self.items:
            idx = getattr(item, "index", None)
            if idx is not None:
                self._by_index[idx] = item

    def add_item(self, item: I):
        idx = getattr(item, "index", None)
        if idx is not None:
            self._by_index[idx] = item
        self.items.append(item)

    def get_item(self, item_index: int):
        return self._by_index.get(item_index)

# ------------------------------------------------------------
# BASE LAYOUT COLLECTION
# ------------------------------------------------------------

class LayoutsBase(Generic[L]):
    header: str = ""

    def __init__(self, layouts: Optional[List[L]] = None):
        self.layouts: List[L] = []
        self._by_index: Dict[int, L] = {}

        if layouts:
            for lay in layouts:
                self.add(lay)

    def add(self, layout: L):
        if layout.index in self._by_index:
            raise ValueError(f"Duplicate layout index {layout.index}")
        self.layouts.append(layout)
        self._by_index[layout.index] = layout

    def get(self, layout_index: int) -> L:
        return self._by_index[layout_index]

    def __iter__(self): return iter(self.layouts)

    def walk_items(self):
        for layout in self.layouts:
            for item in layout.items:
                yield item
                
    def remap(self, *, attr: str, reorder_map: Dict[int, int], collection):
        """Generic remap: beam.elset → new elset; region.material → new material, etc."""
        for layout in self.layouts:
            for item in layout.items:
                old_idx = getattr(getattr(item, attr), "index")
                new_idx = reorder_map[old_idx]
                setattr(item, attr, collection.get(new_idx))


# ------------------------------------------------------------
# GENERIC LAYOUT PARSER
# ------------------------------------------------------------

class LayoutParser(ABC, Generic[M, L, C, I]):

    @classmethod
    @abstractmethod
    def get_collection(cls) -> Type[C]:
        pass

    @classmethod
    @abstractmethod
    def start_of_layout(cls, line: str) -> bool:
        pass

    @classmethod
    @abstractmethod
    def parse_layout_header(cls, line: str) -> L:
        pass

    @classmethod
    @abstractmethod
    def parse_item(cls, line: str, nodes, elsets) -> I:
        pass

    @classmethod
    def get_item_parser(cls):
        return None

    @classmethod
    def reset_local_counter(cls):
        pass

    @classmethod
    def from_model(cls, model: M, nodes, elsets) -> C:
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)

        if not block:
            return collection_cls([])

        layouts: List[L] = []
        current_layout: Optional[L] = None

        item_parser = cls.get_item_parser()  # ✅ explicit

        for raw in block.body:
            line = raw.strip()
            if not line:
                continue

            if cls.start_of_layout(line):
                if current_layout is not None:
                    layouts.append(current_layout)

                current_layout = cls.parse_layout_header(line)

                # ✅ reset local counter per layout
                if item_parser and hasattr(item_parser, "reset_local_counter"):
                    item_parser.reset_local_counter()

                continue

            if current_layout is not None:
                item = cls.parse_item(line, nodes, elsets)
                current_layout.add_item(item)

        if current_layout is not None:
            layouts.append(current_layout)

        return collection_cls(layouts)
  
class LayoutEngine(ABC, Generic[I, L, C]):
    @classmethod
    def _dispatch_transform(
        cls,
        *,
        items: list[I],
        target_layout: L,
        include_original: bool,
        mode: str,
        nodes: Nodes,
        op_kwargs: dict,
    ) -> list[I]:
        raise NotImplementedError

    @classmethod
    def apply(
        cls,
        base_layouts: C,
        layouts_to_modify: C,
        *,
        include_original: bool = True,
        mode: str,
        nodes: Nodes,
        **op_kwargs,
    ) -> C:
        # 1) Build initial layouts from BASE
        new_layouts: list[L] = []
        for layout in base_layouts.layouts:
            items = layout.items.copy() if include_original else []
            new_layouts.append(type(layout)(index=layout.index, items=items))

        by_index: dict[int, L] = {lay.index: lay for lay in new_layouts}

        # 2) For each layout we want to modify, compute transformed items
        for src_layout in layouts_to_modify.layouts:
            target = by_index[src_layout.index]

            # For replicate/mirror: source geometry is layouts_to_modify
            src_items = src_layout.items

            transformed_items = cls._dispatch_transform(
                items=src_items,
                target_layout=target,
                include_original=include_original,
                mode=mode,
                nodes=nodes,
                op_kwargs=op_kwargs,
            )

            # Replace items in the TARGET layout
            target.items = list(transformed_items)

        # 3) Re-index beams within each floor
        for layout in new_layouts:
            for i, item in enumerate(layout.items, start=1):
                item.index = i
            layout.rebuild_index()

        # 4) Return new collection
        return type(base_layouts)(layouts=new_layouts)

    
class LayoutsQuery(Generic[I, L, C]):
    """
    Generic utility for all LayoutsBase collections.
    Works with any LayoutBase + LayoutsBase combination.
    """

    TOL = 1e-6

    # ----------------------------------------------------------------------
    # Layout-level selection
    # ----------------------------------------------------------------------
    @staticmethod
    def get_layouts_by_indices(layouts: C, indices: List[int]) -> C:
        selected = [lay for lay in layouts.layouts if lay.index in set(indices)]
        return type(layouts)(layouts=selected)

    @staticmethod
    def iter_layouts(layouts: C):
        for lay in layouts.layouts:
            yield lay

    # ----------------------------------------------------------------------
    # Item-level utilities
    # ----------------------------------------------------------------------
    @staticmethod
    def iter_items(layouts: C):
        """Yield (item, parent_layout)."""
        for lay in layouts.layouts:
            for item in lay.items:
                yield item, lay

    @staticmethod
    def flatten_items(layouts: C) -> List[I]:
        return [item for item, _ in LayoutsQuery.iter_items(layouts)]

    @staticmethod
    def get_item_by_index(layouts: C, item_index: int) -> Tuple[Optional[I], Optional[L]]:
        for layout in layouts.layouts:
            item = layout.get_item(item_index)
            if item is not None:
                return item, layout
        return None, None

    # ----------------------------------------------------------------------
    # Node-based helpers (for geometry matching)
    # ----------------------------------------------------------------------
    @staticmethod
    def _match_node(a, b, tol=1e-6):
        return (
            abs(a.x - b.x) < tol and
            abs(a.y - b.y) < tol and
            abs(a.z - b.z) < tol
        )

    @classmethod
    def _match_two_node_item(cls, item: I, n1, n2) -> bool:
        """Works for Beams (start/end)."""
        if not hasattr(item, "start") or not hasattr(item, "end"):
            return False

        a, b = item.start, item.end
        tol = cls.TOL

        fwd = (cls._match_node(a, n1, tol) and cls._match_node(b, n2, tol))
        rev = (cls._match_node(a, n2, tol) and cls._match_node(b, n1, tol))

        return fwd or rev

    @classmethod
    def _match_four_node_item(cls, item: I, nodes: Tuple) -> bool:
        """Works for Regions (edges)."""
        edges = getattr(item, "edges", None)
        if edges is None or len(edges) != 4:
            return False

        tol = cls.TOL
        t = nodes

        # Try 4 cyclic rotations
        for shift in range(4):
            ok = True
            for i in range(4):
                a = edges[(shift + i) % 4]
                b = t[i]
                if not cls._match_node(a, b, tol):
                    ok = False
                    break
            if ok:
                return True

        return False

    # ----------------------------------------------------------------------
    # Public: universal geometric search
    # ----------------------------------------------------------------------
    @classmethod
    def find_item_by_nodes(cls, layouts: C, *nodes) -> Tuple[Optional[I], Optional[L]]:
        """
        Universal finder:
        - If len(nodes)==2 → find Beam
        - If len(nodes)==4 → find Region
        """
        if len(nodes) == 2:
            n1, n2 = nodes
            for item, lay in cls.iter_items(layouts):
                if cls._match_two_node_item(item, n1, n2):
                    return item, lay
            return None, None

        if len(nodes) == 4:
            for item, lay in cls.iter_items(layouts):
                if cls._match_four_node_item(item, nodes):
                    return item, lay
            return None, None

        raise ValueError("find_item_by_nodes only supports 2- or 4-node geometry")

    # ----------------------------------------------------------------------
    # Public: predicate search
    # ----------------------------------------------------------------------
    @staticmethod
    def find_item(layouts: C, predicate: Callable[[I], bool]) -> Tuple[Optional[I], Optional[L]]:
        """Return first item matching predicate."""
        for item, lay in LayoutsQuery.iter_items(layouts):
            try:
                if predicate(item):
                    return item, lay
            except Exception:
                pass
        return None, None

class LayoutAdapter(ABC, Generic[M, I, L, C]):

    # ------------------------------
    # MUST IMPLEMENT
    # ------------------------------

    @classmethod
    @abstractmethod
    def update_var(cls, layouts: C, model: M) -> M:
        """
        Optionally update Building variables after exporting.
        Example: building.beam_layout = len(layouts)
        """
        return model

    @classmethod
    @abstractmethod
    def format_layout_header(cls, layout: L) -> str:
        """
        Format a line like:
            FLOOR BEAM LAYOUT #1, Total Beam = 5
        """
        pass

    @classmethod
    @abstractmethod
    def format_item(cls, item: I) -> str:
        """
        Format a single item (e.g., Beam line).
        """
        pass

    # ------------------------------
    # OPTIONAL HOOKS
    # ------------------------------

    @classmethod
    def before_write(cls, layouts: C):
        """Hook for custom preprocessing (optional)."""
        pass

    # ------------------------------
    # GENERIC IMPLEMENTATION
    # ------------------------------

    @classmethod
    def to_string(cls, layouts: C) -> str:
        """Convert entire layouts collection into a block of text."""
        lines = [f"*{layouts.header}*"]

        for layout in layouts.layouts:
            lines.append(cls.format_layout_header(layout))
            for item in layout.items:
                lines.append(cls.format_item(item))

        return "\n".join(lines)

    @classmethod
    def to_block(cls, layouts: C):
        """Produce a BlockAdapter for insertion back into model."""
        lines: List[str] = []

        for layout in layouts.layouts:
            lines.append(cls.format_layout_header(layout))
            for item in layout.items:
                lines.append(cls.format_item(item))

        return BlockAdapter.from_lines(
            header=layouts.header,
            lines=lines
        )

    @classmethod
    def to_model(cls, layouts: C, model: M) -> M:
        """Write layouts back into model.blocks and update vars."""
        cls.before_write(layouts)

        block = cls.to_block(layouts)
        model.blocks[layouts.header] = block

        return cls.update_var(layouts, model)

    # ------------------------------
    # FLOAT HELPERS
    # ------------------------------

    @classmethod
    def _norm_float(cls, value):
        v = float(value)
        return int(v) if v.is_integer() else v

    @classmethod
    def _norm_float_sci(cls, value: float):
        if value.is_integer():
            return int(value)

        if abs(value) < 1e-3 or abs(value) >= 1e4:
            s = f"{value:.15E}"
            base, exp = s.split("E")
            base = base.rstrip("0").rstrip(".")
            return f"{base}E{int(exp):+04d}"

        return value