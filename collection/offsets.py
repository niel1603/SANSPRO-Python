from typing import List, Optional, Type

from SANSPRO.model.model import Model
from SANSPRO.object.offset import Offset
from collection._collection_abstract import Collection, CollectionParser, ObjectCollectionQuery, ObjectCollectionEngine, ObjectCollectionAdapter
from SANSPRO.collection.nodes import Nodes

from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.variable.parameter import ParameterParse, ParameterAdapter
from SANSPRO.collection.diaphragms import DiaphragmsParse, DiaphragmsEngine, DiaphragmsAdapter

class Offsets(Collection[Offset]):
    header = 'OFFSET'
    item_type = Offset
        
class OffsetsParse(CollectionParser[Model, Offset, Offsets]):
    LINES_PER_ITEM = 1
    _offset_counter: int = 0

    @classmethod
    def get_collection(cls) -> Type[Offsets]:
        return Offsets

    @classmethod
    def parse_line(cls, lines: List[str], nodes: Nodes) -> Offset:
        tokens = [line.strip().split() for line in lines]
        return cls._parse_offset(tokens, nodes=nodes)

    @classmethod
    def _parse_offset(cls, tokens: List[List[str]], nodes: Nodes) -> Offset:
        l0 = tokens[0]
        cls._offset_counter += 1
        index = cls._offset_counter

        return Offset(
            index=int(index),
            floor=int(l0[0]),
            node=nodes.get(int(l0[1])),
            x=float(l0[3]),
            y=float(l0[2]),
            z=float(l0[4]),
        )
    
    @classmethod
    def from_model(cls, model: Model, nodes: Nodes) -> Offsets:
        block = model.blocks.get(cls.get_collection().header)
        lines = block.body
        offsets: list[Offset] = []
        cls._offset_counter = 0

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            region = cls.parse_line([raw_line], nodes=nodes)
            offsets.append(region)

        return Offsets(offsets)
    
class OffsetsAdapter(ObjectCollectionAdapter[Model, Offset, Offsets]):

    @classmethod
    def update_var(cls, offsets: Offsets, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.height_offset = len(offsets.objects)
        model = BuildingAdapter.to_model(building, model)
        return model

    @classmethod
    def format_line(cls, offset: Offset) -> str:
        f = offset.floor
        n = offset.node.index
        x = cls._norm_float(offset.x)
        y = cls._norm_float(offset.y)
        z = cls._norm_float(offset.z)
        return f"   {f}     {n}  {y} {x} {z}"