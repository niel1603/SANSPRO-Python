
from typing import Type, List

from SANSPRO.model.model import Model
from SANSPRO.object.slab import Region
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.slabs import Slabs

from SANSPRO.variable.building import BuildingParse, BuildingAdapter

from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

class Regions(Collection[Region]):
    header = "REGION"

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