from typing import Type, List

from SANSPRO.model.model import Model
from SANSPRO.object.beam import Beam
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets
from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

class Beams(Collection[Beam]):
    header = "FLOOR BEAM LAYOUT"

class BeamsParse(CollectionParser[Model, Beam, Beams]):
    """Parses single beam lines within a FLOOR BEAM LAYOUT block."""
    LINES_PER_ITEM = 1
    _beam_counter: int = 0  # internal static counter

    @classmethod
    def reset_local_counter(cls):
        cls._beam_counter = 0

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