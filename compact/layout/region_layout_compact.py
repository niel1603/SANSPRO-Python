from dataclasses import dataclass

from SANSPRO.compact.layout._layout_compact import CompactLayoutBase, CompactLayoutsBase

from SANSPRO.object.slab import SlabSupportOption, Region
from SANSPRO.layout.regions import Regions

from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.slabs import Slabs
from SANSPRO.collection.elsets import Elsets

@dataclass
class RegionCompact:
    layout: int
    floor: int
    node1: int
    node2: int
    node3: int
    node4: int
    slab: int
    support_option: int

@dataclass
class CompactRegionLayout(CompactLayoutBase[RegionCompact]):

    @classmethod
    def from_layout(cls, full: Regions) -> "CompactRegionLayout":
        compact_items = [
            RegionCompact(
                layout=int(1),
                floor=c.floor,
                node1=c.edges[0].index,
                node2=c.edges[1].index,
                node3=c.edges[2].index,
                node4=c.edges[3].index,
                slab=c.slab.index,
                support_option=int(c.option),
            )
            for c in full.objects
        ]

        return cls(
            index=1,
            items=compact_items,
        )
    
    def to_full(self, *, nodes: Nodes, slabs: Slabs, start_index: int = 1) -> Regions:
        full_items = []
        idx = start_index
        for c in self.items:
            beam = Region(
                index=idx,
                floor=int(c.floor),
                slab=slabs.get(c.slab),
                option=SlabSupportOption(int(c.support_option)),
                qDL_add=float(0),
                qLL_add=float(0),
                edges= [nodes.get(int(c.node1)), nodes.get(int(c.node2)), nodes.get(int(c.node3)), nodes.get(int(c.node4))],
                offset=int(0),
                misc=str('0,0,1 0 0 3 -')
            )
            full_items.append(beam)
            idx += 1

        return Regions(
            objects=full_items,
        )

class CompactRegionLayouts(CompactLayoutsBase[CompactRegionLayout]):

    @classmethod
    def from_layouts(cls, full_layouts: Regions) -> "CompactRegionLayouts":
        result = cls()
        compact = CompactRegionLayout.from_layout(full_layouts)
        result.add(compact)
        return result
    
    def to_full(self, *, nodes, slabs) -> Regions:
        result = Regions()
        for compact_layout in self.layouts:
            full = compact_layout.to_full(
                nodes=nodes,
                slabs=slabs,
                start_index=1
            )
            result.extend(full.objects)
        return result