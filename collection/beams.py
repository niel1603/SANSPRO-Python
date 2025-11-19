from typing import Optional, Type, List, Dict

from SANSPRO.model.Model import Model
from SANSPRO.object.beam import Beam, BeamLayout
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

class Beams(Collection[Beam]):
    header = "FLOOR BEAM LAYOUT"


class BeamLayouts(Collection[BeamLayout]):
    header = "LAYBEAM"

# ==========================================================
# SINGLE BEAM PARSER
# ==========================================================

class BeamsParse(CollectionParser[Model, Beam, Beams]):
    """Parses single beam lines within a FLOOR BEAM LAYOUT block."""
    LINES_PER_ITEM = 1
    _beam_counter: int = 0  # internal static counter

    @classmethod
    def get_collection(cls) -> Type[Beams]:
        return Beams

    @classmethod
    def parse_line(cls, lines: List[str], **kwargs) -> Beam:
        raw_line = lines[0]
        tokens = [raw_line.strip().split()]

        nodes: Nodes = kwargs.get("nodes")
        elsets: Elsets = kwargs.get("elsets")

        if nodes is None or elsets is None:
            raise ValueError("BeamsParse requires both 'nodes' and 'elsets' collections")

        return cls._parse_beam(raw_line, tokens, nodes, elsets)

    # ----------------------------------------------------------
    @classmethod
    def _parse_beam(cls, raw_line: str, tokens: List[List[str]], nodes: Nodes, elsets: Elsets) -> Beam:
        cls._beam_counter += 1
        index = cls._beam_counter

        l0 = tokens[0]
        start_index = int(l0[0])
        end_index = int(l0[1])
        elset_index = int(l0[2])
        group = int(l0[3])
        beam_type = int(l0[4])

        # preserve everything after the fifth token
        misc = raw_line.split(None, 5)[-1] if len(raw_line.split(None, 5)) > 5 else ""

        start_node = nodes.get(start_index)
        end_node = nodes.get(end_index)
        elset = elsets.get(elset_index)

        if start_node is None or end_node is None:
            raise ValueError(f"Beam {index} references missing nodes {start_index}, {end_index}")
        if elset is None:
            raise ValueError(f"Beam {index} references missing elset {elset_index}")

        return Beam(
            index=index,
            start=start_node,
            end=end_node,
            elset=elset,
            group=group,
            beam_type=beam_type,
            misc=misc,
        )

    @classmethod
    def from_model(cls, model: Model, nodes: Nodes, elsets: Elsets) -> Beams:
        cls._beam_counter = 0
        return super().from_model(model, nodes=nodes, elsets=elsets)
    
class BeamsAdapter(ObjectCollectionAdapter[Model, Beam, Beams]):

    @classmethod
    def format_line(cls, beam: Beam) -> str:
        st = int(beam.start.index)
        en = int(beam.end.index)
        e = int(beam.elset.index)
        g = int(beam.group)
        bt = int(beam.beam_type)
        misc = str(beam.misc)

        line = f'{st:>5} {en:>3} {e:>2} {g:>2} {bt} {misc}'
        return line

# ==========================================================
# MULTI-LAYOUT BEAM PARSER
# ==========================================================

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
        

