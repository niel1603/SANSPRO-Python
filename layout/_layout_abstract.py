# _layout_abstract.py

from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Type, List, Optional, Dict

from SANSPRO.model.model import Model, BlockAdapter
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
        for item in self.items:
            idx = getattr(item, "index", None)
            if idx is not None:
                self._by_index[idx] = item

    def __len__(self): return len(self.items)
    def __iter__(self): return iter(self.items)

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