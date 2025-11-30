from typing import Type, List, Dict

from SANSPRO.model.model import Model
from object.slab import Slab, Region
from SANSPRO.object.node import Node
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets
from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

from SANSPRO.variable.building import BuildingParse, BuildingAdapter

class Slabs(Collection[Slab]):
    header = "FLOORSLAB"
    item_type = Slab


class SlabsParse(CollectionParser[Model, Slab, Slabs]):
    """Parse *FLOORSLAB* block, embedding Elset references."""
    LINES_PER_ITEM = 1
    _slab_counter: int = 0

    @classmethod
    def get_collection(cls) -> Type[Slabs]:
        return Slabs

    @classmethod
    def from_model(cls, model: Model, elsets: Elsets) -> Slabs:
        """Parse *FLOORSLAB* with Elset embedding."""
        block = model.blocks.get(cls.get_collection().header)
        if block is None:
            raise ValueError("Model missing 'FLOORSLAB' block")

        lines = block.body
        slabs: list[Slab] = []
        cls._slab_counter = 0

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            slab = cls.parse_line([raw_line], elsets=elsets)
            slabs.append(slab)

        return Slabs(slabs)

    @classmethod
    def parse_line(cls, lines: List[str], **kwargs) -> Slab:
        """Parse a single line of *FLOORSLAB*."""
        raw_line = lines[0]
        tokens = [raw_line.strip().split()]
        elsets: Elsets = kwargs.get("elsets")

        if elsets is None:
            raise ValueError("SlabsParse requires 'elsets' collection")

        return cls._parse_slab(tokens, elsets)

    @classmethod
    def _parse_slab(cls, tokens: List[List[str]], elsets: Elsets) -> Slab:
        cls._slab_counter += 1
        l0 = tokens[0]

        index = int(l0[0])
        name = str(l0[1])
        slab_type = int(l0[2])
        elset_index = int(l0[3])
        thick = float(l0[4])
        qDL = float(l0[5])
        qLL = float(l0[6])
        weight = float(l0[7])
        cost = float(l0[8])

        # 🔹 Embed Elset object directly
        elset = elsets.get(elset_index)
        if elset is None:
            raise ValueError(f"Elset {elset_index} not found for slab {index}")

        return Slab(
            index=index,
            name=name,
            slab_type=slab_type,
            elset=elset,
            thick=thick,
            qDL=qDL,
            qLL=qLL,
            weight=weight,
            cost=cost,
        )
    
    @staticmethod
    def remap_elsets(slabs: Slabs,
                     reorder_map: Dict[int, int],
                     new_elsets: Elsets):

        for slab in slabs.objects:
            old_idx = slab.elset.index

            if old_idx not in reorder_map:
                raise KeyError(
                    f"[SlabsParse.remap_elsets] Missing map for old elset {old_idx}"
                )

            new_idx = reorder_map[old_idx]
            new_elset = new_elsets.get(new_idx)

            if new_elset is None:
                raise KeyError(
                    f"[SlabsParse.remap_elsets] "
                    f"Mapped elset {new_idx} not found in merged_elsets"
                )

            slab.elset = new_elset

class SlabsAdapter(ObjectCollectionAdapter[Model, Slab, Slabs]):

    @classmethod
    def update_var(cls, slabs: Slabs, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.slab_data = len(slabs.objects)
        model = BuildingAdapter.to_model(building, model)

        return model

    @classmethod
    def format_line(cls, s: Slab) -> str:
        i    = int(s.index)
        nm   = str(s.name)
        sl_t = int(s.slab_type)
        els  = int(s.elset.index)

        thk  = cls._norm_float(s.thick) 
        q_dl = cls._norm_float(s.qDL)
        q_ll = cls._norm_float(s.qLL)
        wgt  = cls._norm_float(s.weight)
        cst  = cls._norm_float(s.cost)

        line = f'{i:>4}  {nm:<10} {sl_t} {els:>2} {thk} {q_dl} {q_ll} {wgt} {cst}'
        return line
