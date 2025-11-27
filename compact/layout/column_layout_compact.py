from dataclasses import dataclass

from SANSPRO.compact.layout._layout_compact import CompactLayoutBase, CompactLayoutsBase

from SANSPRO.object.column import Column
from SANSPRO.layout.column_layout import ColumnLayout, ColumnLayouts

from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets

@dataclass
class ColumnCompact:
    layout: int
    location: int
    elset: int
    alpha: int

@dataclass
class CompactColumnLayout(CompactLayoutBase[ColumnCompact]):

    @classmethod
    def from_layout(cls, full: ColumnLayout) -> "CompactColumnLayout":
        compact_items = [
            ColumnCompact(
                layout=full.index,
                location=c.location.index,
                elset=c.elset.index,
                alpha=c.alpha
            )
            for c in full.items
        ]

        return cls(
            index=full.index,
            items=compact_items,
        )
    
    def to_full(self, *, nodes: Nodes, elsets: Elsets, start_index: int = 1) -> "ColumnLayout":
        full_items = []
        idx = start_index
        for c in self.items:
            beam = Column(
                index=idx,
                location=nodes.get(c.location),
                elset=elsets.get(c.elset),
                group= int(0),
                alpha=int(c.alpha),
                misc=str('1 0 0 0 0 -1 -1 0 0 0  1.20  1.20 0 0    0.0    0.0    0.0    0.0 0 0 0 0 0 0 0 0 0 0 0 0 0    0.000 0.000 0 0 0,0   0.00,  0.00')
            )
            full_items.append(beam)
            idx += 1

        return ColumnLayout(
            index=self.index,
            items=full_items,
        )

class CompactColumnLayouts(CompactLayoutsBase[CompactColumnLayout]):

    @classmethod
    def from_layouts(cls, full_layouts: ColumnLayouts) -> "CompactColumnLayouts":
        result = cls()
        for full in full_layouts:
            compact = CompactColumnLayout.from_layout(full)
            result.add(compact)
        return result
    
    def to_full(self, *, nodes, elsets) -> ColumnLayouts:
        result = ColumnLayouts()
        for compact_layout in self.layouts:
            full = compact_layout.to_full(
                nodes=nodes,
                elsets=elsets,
                start_index=1
            )
            result.add(full)
        return result