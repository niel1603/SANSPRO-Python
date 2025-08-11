from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type, TypeVar, Generic, Union

from Model.Model import Model, BlockAdapter
from Object.ObjectAbstract import Object

M = TypeVar('M', bound='Model')
T = TypeVar('T', bound='Object')
C = TypeVar('C', bound='Collection[Object]')

class Collection(Generic[T]):

    header : str = ""

    def __init__(self, objects: Optional[List[T]] = None):
        self.objects: List[T] = []
        self._index: Dict[int, T] = {}
        self._reverse_index: Dict[int, int] = {}

        if objects:
            self._initialize(objects)

    def _initialize(self, objects: List[T]):
        for obj in objects:
            self.objects.append(obj)
            self._index[obj.index] = obj
            self._reverse_index[id(obj)] = obj.index

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

    def index(self, index: int) -> Optional[T]:
        return self._index.get(index)

class CollectionParser(ABC, Generic[M, T, C]):

    @classmethod
    @abstractmethod
    def get_collection(cls) -> Type[C]:
        pass

    @classmethod
    @abstractmethod
    def parse_line(cls, line: str) -> T:
        pass
    
    @classmethod
    def from_model(cls, model: M) -> C:
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)
        parsed_items: List[T] = []

        for line in block.body:
            parsed_item = cls.parse_line(line)
            parsed_items.append(parsed_item)

        return collection_cls(parsed_items)


class ObjectCollectionAdapter(ABC, Generic[M, T, C]):

    @classmethod
    def norm_float(cls, value: float) -> Union[int, float]:
        return int(value) if value.is_integer() else value
    
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