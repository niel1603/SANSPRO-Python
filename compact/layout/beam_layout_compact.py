from dataclasses import dataclass

from SANSPRO.compact.layout._layout_compact import CompactLayoutBase, CompactLayoutsBase

from SANSPRO.object.beam import Beam
from SANSPRO.layout.beam_layout import BeamLayout, BeamLayouts

from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets

@dataclass
class BeamCompact:
    layout: int
    start: int
    end: int
    elset: int

@dataclass
class CompactBeamLayout(CompactLayoutBase[BeamCompact]):

    @classmethod
    def from_layout(cls, full: BeamLayout) -> "CompactBeamLayout":
        compact_items = [
            BeamCompact(
                layout=full.index,
                start=b.start.index,
                end=b.end.index,
                elset=b.elset.index,
            )
            for b in full.items
        ]

        return cls(
            index=full.index,
            items=compact_items,
        )
    
    def to_full(self, *, nodes: Nodes, elsets: Elsets, start_index: int = 1) -> "BeamLayout":
        full_items = []
        idx = start_index
        for c in self.items:
            beam = Beam(
                index=idx,
                start=nodes.get(c.start),
                end=nodes.get(c.end),
                elset=elsets.get(c.elset),
                group= int(0),
                beam_type= int(1),
                misc=str('0 0 0 0 0 1 0 DWGLABEL   -1.0   -1.0  1.20  1.20 0 0   0.0 100.0   0.0   6.0 0 0 0 0    0.0    0.0    0.0    0.0 0 0 0 0 0 0 0 0 0 0 0 0 0 0    0.000 0.000 0 0 0  0 0    0.00   0.00')
            )
            full_items.append(beam)
            idx += 1

        return BeamLayout(
            index=self.index,
            items=full_items,
        )

class CompactBeamLayouts(CompactLayoutsBase[CompactBeamLayout]):

    @classmethod
    def from_layouts(cls, full_layouts: BeamLayouts) -> "CompactBeamLayouts":
        result = cls()
        for full in full_layouts:
            compact = CompactBeamLayout.from_layout(full)
            result.add(compact)
        return result
    
    def to_full(self, *, nodes, elsets) -> BeamLayouts:
        result = BeamLayouts()
        for compact_layout in self.layouts:
            full = compact_layout.to_full(
                nodes=nodes,
                elsets=elsets,
                start_index=1
            )
            result.add(full)
        return result