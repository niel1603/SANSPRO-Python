import re
from abc import ABC, abstractmethod
from dataclasses import asdict

from typing import List, Dict, Optional, Type, TypeVar, Generic, Union, Callable, Any, Set, Tuple

from SANSPRO.model.Model import Model, BlockAdapter
from SANSPRO.object.ObjectAbstract import Object

M = TypeVar('M', bound='Model')
T = TypeVar('T', bound='Object')
C = TypeVar('C', bound='Collection[Object]')

class Collection(Generic[T]):

    header: str = ""

    def __init__(self, objects: Optional[List[T]] = None):
        self.objects: List[T] = []
        self._index: Dict[int, T] = {}
        self._reverse_index: Dict[int, int] = {}

        if objects:
            self._initialize(objects)

    def _initialize(self, objects: List[T]):
        for obj in objects:
            self.add(obj)

    def add(self, obj: T):
        self.objects.append(obj)
        self._index[obj.index] = obj
        self._reverse_index[id(obj)] = obj.index

    def remove(self, obj: T):
        if obj in self.objects:
            self.objects.remove(obj)
            self._index.pop(obj.index, None)
            self._reverse_index.pop(id(obj), None)

    def extend(self, objs: List[T]):
        for obj in objs:
            self.add(obj)

    def index_list(self) -> List[int]:
        return sorted(self._index.keys())

    def get(self, index: int) -> Optional[T]:
        return self._index.get(index)

    def __getitem__(self, index: int) -> T:
        return self._index[index]

    def __contains__(self, index: int) -> bool:
        return index in self._index

    def __iter__(self):
        return iter(self.objects)
    

    # ==========================================================
    # SUMMARY UTILITIES
    # ==========================================================
    def summary(self) -> str:
        """Return a compact summary of all available indices."""
        ids = sorted(self._index.keys())
        return print(f"{self.header or 'Collection'}: {len(ids)} items, indices = {ids}")
    
    # ==========================================================
    # 🔹 Strict Elset Collector
    # ==========================================================
    def get_used_elsets(self) -> Set[int]:
        """
        Return all unique Elset indices referenced by this collection.
        Supports both flat and layered collections (e.g., BeamLayouts).
        Raises AttributeError if no elset references are found.
        """
        if not self.objects:
            return set()

        used: set[int] = set()
        found_any = False

        for obj in self.objects:
            # --- Case 1: object directly has .elset
            if hasattr(obj, "elset"):
                elset = getattr(obj, "elset")
                if elset is not None:
                    used.add(elset.index)
                    found_any = True

            # --- Case 2: object has nested list/collection with elset references
            else:
                for attr_name, attr_value in vars(obj).items():
                    if isinstance(attr_value, list):
                        for item in attr_value:
                            if hasattr(item, "elset"):
                                elset = getattr(item, "elset")
                                if elset is not None:
                                    used.add(elset.index)
                                    found_any = True

        if not found_any:
            raise AttributeError(
                f"{type(self).__name__} does not contain (or wrap) objects with an 'elset' attribute"
            )

        return used
    
    # ==========================================================
    # NAME LOOKUP UTILITIES
    # ==========================================================
    def _ensure_name_index(self):
        """
        Build a name → object lookup table.
        Only objects with a .name attribute are included.
        """
        self._name_index = {}

        for obj in self.objects:
            if hasattr(obj, "name"):
                self._name_index[obj.name] = obj

    def get_by_name(self, name: str):
        """
        Soft name lookup.
        Returns the object whose .name equals `name`, or None if not found.

        Raises:
            AttributeError if objects do not have .name at all.
        """

        if not self.objects:
            return None

        first = self.objects[0]
        if not hasattr(first, "name"):
            raise AttributeError(
                f"{type(self).__name__} objects do not define a 'name' attribute"
            )

        # rebuild table each time (safe & fresh)
        for obj in self.objects:
            if hasattr(obj, "name") and obj.name == name:
                return obj

        return None  # <── IMPORTANT

class CollectionParser(ABC, Generic[M, T, C]):

    @classmethod
    @abstractmethod
    def get_collection(cls) -> Type[C]:
        pass

    @classmethod
    @abstractmethod
    def parse_line(cls, lines: List[str], **kwargs) -> T:
        pass

    @classmethod
    def from_model(cls, model: M, **kwargs) -> C:
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)
        parsed_items: list[T] = []

        n = getattr(cls, "LINES_PER_ITEM", 1)
        lines = block.body

        for i in range(0, len(lines), n):
            item_lines = lines[i:i + n]
            try:
                parsed_item = cls.parse_line(item_lines, **kwargs)
            except Exception:
                import traceback; traceback.print_exc()
                parsed_item = None

            if parsed_item:
                parsed_items.append(parsed_item)

        return collection_cls(parsed_items)
    
    # Older version, perfectly able to handle one line text
    # for example *NODEXY*


    # @classmethod
    # def from_model(cls, model: M) -> C:
    #     collection_cls = cls.get_collection()
    #     block = SANSPRO.model.blocks.get(collection_cls.header)
    #     parsed_items: List[T] = []

    #     print('block:')
    #     print(block)

    #     for i, line in enumerate(block.body, start=1):
    #         print(f"\n[DEBUG] Line {i}: {repr(line)}")
    #         parts = line.split()
    #         print(f"[DEBUG] Split parts: {parts}")

    #         parsed_item = cls.parse_line(line)
    #         print(f"[DEBUG] Parsed item: {parsed_item}")

    #         parsed_items.append(parsed_item)

    # New version, try to adapt to the multiple line definition
    # for example *SECTION*


class ObjectCollectionAdapter(ABC, Generic[M, T, C]):
  
    @classmethod
    @abstractmethod
    def update_var(cls, collection: C, model: M) -> M:
        return model

    @classmethod
    @abstractmethod
    def format_line(cls, obj: T) -> str:
        pass
    
    @classmethod
    def to_string(cls, collection: C) -> str:
        lines = [f'*{collection.header}*']
        for obj in collection.objects:
            lines.append(cls.format_line(obj))
        return "\n".join(lines)
    
    @classmethod
    def to_block(cls, collection: C) -> str:
        header = collection.header
        lines = []
        for obj in collection.objects:
            lines.append(cls.format_line(obj))
        return BlockAdapter.from_lines(header= header, lines= lines)
    
    @classmethod
    def to_model(cls, collection: C, model: M) -> M:
        header = collection.header
        lines = []

        for obj in collection.objects:
            lines.append(cls.format_line(obj))

        block = BlockAdapter.from_lines(header= header, lines= lines)
        model.blocks[header] = block
        model = cls.update_var(collection, model)
        return model
    
    # @classmethod
    # def _norm_float(cls, value: float) -> Union[int, float]:
    #     return int(value) if value.is_integer() else value

    @classmethod
    def _norm_float(cls, value) -> Union[int, float]:
        value = float(value)
        return int(value) if value.is_integer() else value
    
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
    
class ObjectCollectionQuery(ABC, Generic[T, C]):
    
    @staticmethod
    @abstractmethod
    def get_by_indices(collection: C, indices: List[int]) -> C:
        """Return a subset of the collection containing objects matching the indices."""
        pass

    @staticmethod
    @abstractmethod
    def get_by_offset(collection: C, dx: float, dy: float, dz: float,
                      origin: Optional[T] = None) -> Optional[T]:
        """Return an object offset by (dx, dy, dz) from origin in the collection."""
        pass

    @staticmethod
    @abstractmethod
    def select_by_polygon(collection: C, boundary_indices: List[int]) -> C:
        """Return a subset of the collection that falls inside the polygon defined by boundary indices."""
        pass

class ObjectCollectionEngine(ABC, Generic[T, C]):

    @staticmethod
    @abstractmethod
    def replicate(base_collection: C,
                  selected_objects: C,
                  *args, **kwargs) -> C:
        """Replicate selected_objects within base_collection under given params."""
        pass

    @staticmethod
    @abstractmethod
    def extend(base_collection: C,
               target_index: int,
               *args, **kwargs) -> C:
        """Extend base_collection with new objects up to target_index."""
        pass
class CollectionComparer(ABC, Generic[M, T, C]):

    def __init__(self, existing, imported):
        self.existing = existing
        self.imported = imported

    @staticmethod
    def get_sort_key(obj):
        if hasattr(obj, "name"):
            return obj.name.lower()
        return float("inf")

    def merge_and_reorder(
        self,
        key: Callable[[T], Any] = None,
        unique_attr: str = "name",
        remove_missing: bool = False,
        used_elsets: Optional[Set[int]] = None,
    ) -> Tuple[C, Dict[int, int], bool]:

        used_elsets = used_elsets or set()
        key = key or self.get_sort_key

        existing_lookup = {
            getattr(o, unique_attr): o for o in self.existing.objects
        }
        imported_lookup = {
            getattr(o, unique_attr): o for o in self.imported.objects
        }

        # 🔹 snapshot original indices BEFORE we mutate anything
        old_index_by_name: dict[str, int] = {
            name: obj.index for name, obj in existing_lookup.items()
        }

        merged: list[T] = []

        # --------------------------------------------------------
        # Step 1: existing items (with removal rules + overwrite)
        # --------------------------------------------------------
        for name, old_obj in existing_lookup.items():

            if name in imported_lookup or old_obj.index in used_elsets:
                if name in imported_lookup:
                    imp_obj = imported_lookup[name]
                    # overwrite properties from imported → existing
                    self._copy_attributes_overwriting(old_obj, imp_obj)
                merged.append(old_obj)
            else:
                # missing + unused → dropped
                pass

        # --------------------------------------------------------
        # Step 2: add NEW imported items
        # --------------------------------------------------------
        for name, imp_obj in imported_lookup.items():
            if name not in existing_lookup:
                merged.append(imp_obj)

        # --------------------------------------------------------
        # Step 3: sort
        # --------------------------------------------------------
        merged_sorted = sorted(merged, key=key)

        # Build name → new index
        name_to_new_index: dict[str, int] = {
            getattr(obj, unique_attr): idx
            for idx, obj in enumerate(merged_sorted, start=1)
        }

        # --------------------------------------------------------
        # Step 4: build reorder_map using ORIGINAL indices
        # --------------------------------------------------------
        reorder_map: dict[int, int] = {}
        for name, old_idx in old_index_by_name.items():
            if name in name_to_new_index:
                reorder_map[old_idx] = name_to_new_index[name]
            # else: that existing object was removed

        # --------------------------------------------------------
        # Step 5: now rewrite indices to new positions
        # --------------------------------------------------------
        for idx, obj in enumerate(merged_sorted, start=1):
            obj.index = idx

        # --------------------------------------------------------
        # Step 6: wrap
        # --------------------------------------------------------
        collection_cls = type(self.existing)
        merged_collection = collection_cls(merged_sorted)

        removed_any = len(reorder_map) != len(self.existing.objects)

        return merged_collection, reorder_map, removed_any

    # ------------------------------------------------------------
    # Copy imported fields INTO existing, but keep index intact
    # ------------------------------------------------------------
    @staticmethod
    def _copy_attributes_overwriting(existing_obj, imported_obj):
        for attr, value in imported_obj.__dict__.items():
            if attr == "index":
                continue  # NEVER overwrite index
            setattr(existing_obj, attr, value)
