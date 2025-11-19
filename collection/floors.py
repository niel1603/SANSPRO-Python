from typing import Type, List, Dict

from SANSPRO.model.Model import Model
from SANSPRO.object.floor import Slab, Region
from SANSPRO.object.Node import Node
from SANSPRO.collection.Nodes import Nodes
from SANSPRO.collection.elsets import Elsets
from SANSPRO.collection.CollectionAbstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

from SANSPRO.variable.Building import BuildingParse, BuildingAdapter

class Slabs(Collection[Slab]):
    header = "FLOORSLAB"

class Regions(Collection[Region]):
    header = "REGION"

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

class RegionsParse(CollectionParser[Model, Region, Regions]):
    """Parses *REGION* block — flat collection but modeled like a layout parser."""
    LINES_PER_ITEM = 1
    _region_counter: int = 0

    @classmethod
    def get_collection(cls) -> Type[Regions]:
        return Regions

    @classmethod
    def from_model(cls, model: Model, nodes: Nodes, slabs: Slabs) -> Regions:
        block = model.blocks.get(cls.get_collection().header)
        lines = block.body
        regions: list[Region] = []
        cls._region_counter = 0

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            region = cls.parse_line([raw_line], nodes=nodes, slabs=slabs)
            regions.append(region)

        return Regions(regions)

    # ----------------------------------------------------------
    @classmethod
    def parse_line(cls, lines: List[str], **kwargs) -> Region:
        raw_line = lines[0]
        tokens = [raw_line.strip().split()]
        nodes: Nodes = kwargs.get("nodes")
        slabs: Slabs = kwargs.get("slabs")

        if nodes is None or slabs is None:
            raise ValueError("RegionsParse requires both 'nodes' and 'slabs' collections")

        return cls._parse_region(raw_line, tokens, nodes, slabs)

    @classmethod
    def _parse_region(
        cls, raw_line: str, tokens: List[List[str]], nodes: Nodes, slabs: Slabs
    ) -> Region:
        cls._region_counter += 1
        index = cls._region_counter
        l0 = tokens[0]

        floor = int(l0[0])
        slab_index = int(l0[1])
        slab = slabs.get(slab_index)
        option = int(l0[2])
        qDL_add = float(l0[3])

        # ----------------------------------------------------------
        # Explicitly parse 4 edge nodes (always present)

        node1 = nodes.get(int(l0[4].rstrip(",")))
        node2 = nodes.get(int(l0[5].rstrip(",")))
        node3 = nodes.get(int(l0[6].rstrip(",")))
        node4 = nodes.get(int(l0[7].rstrip(",")))
        edges = (node1, node2, node3, node4)

        # ----------------------------------------------------------
        # Parse offset and qLL_add
        # ----------------------------------------------------------
        offset = int(l0[8])
        qLL_add = float(l0[9])

        # ----------------------------------------------------------
        # Preserve everything after qLL_add as misc (full spacing)
        # ----------------------------------------------------------
        misc = raw_line.split(None, 10)[-1]

        return Region(
            index=index,
            floor=floor,
            slab=slab,
            option=option,
            qDL_add=qDL_add,
            qLL_add=qLL_add,
            edges=edges,
            offset=offset,
            misc=misc,
        )

    @staticmethod
    def remap_elsets(regions: Regions):
        """
        Regions reference Slabs, so no direct remap. 
        This function only checks consistency after slab remapping.
        """

        for region in regions.objects:
            if region.slab.elset is None:
                raise ValueError(
                    f"[RegionsParse.remap_elsets] Region {region.index} slab "
                    f"{region.slab.index} has no elset after remapping"
                )
            
class RegionsAdapter(ObjectCollectionAdapter[Model, Region, Regions]):

    @classmethod
    def update_var(cls, regions: Regions, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.slab_region = len(regions.objects)
        model = BuildingAdapter.to_model(building, model)

        return model

    @classmethod
    def format_line(cls, r: Region) -> str:
        flr  = int(r.floor)
        slb  = int(r.slab.index)
        opt  = int(r.option)

        qdla = cls._norm_float(r.qDL_add)
        qlla = cls._norm_float(r.qLL_add)

        n1, n2, n3, n4 = r.edges

        e1 = int(n1.index)
        e2 = int(n2.index)
        e3 = int(n3.index)
        e4 = int(n4.index)

        ofs  = int(r.offset)
        msc  = str(r.misc)

        line = f'   {flr}  {slb} {opt} {qdla}  {e1:>2}, {e2:>2}, {e3:>2}, {e4:>2} {ofs} {qlla}  {msc}'
        return line