from typing import Optional, Type, Dict

from SANSPRO.model.model import Model
from SANSPRO.object.beam import Beam, BeamLayout
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets

from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.collection.beams import Beams, BeamsParse, BeamsAdapter

from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

class BeamLayouts(Collection[BeamLayout]):
    header = "LAYBEAM"

class BeamLayoutsParse(CollectionParser[Model, BeamLayout, BeamLayouts]):
    """Parser for *LAYBEAM* blocks (multi-layout)."""

    @classmethod
    def get_collection(cls) -> Type[BeamLayouts]:
        return BeamLayouts

    @classmethod
    def from_model(cls, model: Model, nodes: Nodes, elsets: Elsets) -> BeamLayouts:
        """Parse multi-layout *LAYBEAM* block."""
        block = model.blocks.get(cls.get_collection().header)
        if block is None:
            raise ValueError("Model missing 'LAYBEAM' block")

        lines = block.body
        layouts: list[BeamLayout] = []

        BeamsParse._beam_counter = 0  # reset shared counter

        current_layout: Optional[BeamLayout] = None
        current_beams: list[Beam] = []

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            # Detect layout header
            if stripped.startswith(Beams.header):
                # finalize previous layout
                if current_layout is not None:
                    current_layout.beams = current_beams
                    layouts.append(current_layout)
                    current_beams = []

                # parse layout header
                parts = stripped.split(",")
                layout_no = int(parts[0].split("#")[1])
                total_beams = int(parts[1].split("=")[1])
                current_layout = BeamLayout(
                    index=layout_no,
                    total_beams=total_beams,
                    beams=[],
                )

            # Parse beam line
            elif stripped[0].isdigit():
                beam = BeamsParse.parse_line([raw_line], nodes=nodes, elsets=elsets)
                current_beams.append(beam)

        # finalize last layout
        if current_layout is not None:
            current_layout.beams = current_beams
            layouts.append(current_layout)

        return BeamLayouts(layouts)
    
    @staticmethod
    def remap_elsets(beam_layouts: BeamLayouts,
                     reorder_map: Dict[int, int],
                     new_elsets: Elsets):
        """
        Update all Beam.elset references according to reorder_map (old→new),
        using new_elsets as the canonical lookup.
        """

        for layout in beam_layouts.objects:
            for beam in layout.beams:
                old_idx = beam.elset.index

                if old_idx not in reorder_map:
                    raise KeyError(f"[BeamLayoutsParse.remap_elsets] "
                                   f"Missing map for old elset {old_idx}")

                new_idx = reorder_map[old_idx]
                new_elset = new_elsets.get(new_idx)
                
                if new_elset is None:
                    raise KeyError(f"[BeamLayoutsParse.remap_elsets] "
                                   f"Mapped elset {new_idx} not found in merged_elsets")

                beam.elset = new_elset

class BeamLayoutsAdapter(ObjectCollectionAdapter[Model, BeamLayout, BeamLayouts]):

    @classmethod
    def update_var(cls, layouts: BeamLayouts, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.beam_layout = len(layouts.objects)
        model = BuildingAdapter.to_model(building, model)

        return model

    @classmethod
    def format_line(cls, layout: BeamLayout) -> str:

        header = f'  FLOOR BEAM LAYOUT #{layout.index}, Total Beam = {layout.total_beams}'
        lines = [header]

        # Append each beam line
        for beam in layout.beams:
            bline = BeamsAdapter.format_line(beam)
            lines.append(bline)

        lines = "\n".join(lines)
        return lines 