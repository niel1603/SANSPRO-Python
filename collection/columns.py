from typing import Type, List

from SANSPRO.model.model import Model
from SANSPRO.object.column import Column
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.elsets import Elsets
from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

class Columns(Collection[Column]):
    header = "COLUMN LAYOUT"

class ColumnsParse(CollectionParser[Model, Column, Columns]):
    """Parses single-column lines inside a COLUMN LAYOUT block."""
    LINES_PER_ITEM = 1
    _col_counter: int = 0

    @classmethod
    def reset_local_counter(cls):
        cls._col_counter = 0

    @classmethod
    def get_collection(cls) -> Type[Columns]:
        return Columns

    @classmethod
    def parse_line(cls, lines: List[str], **kwargs) -> Column:
        raw_line = lines[0]
        tokens = [raw_line.strip().split()]

        nodes: Nodes = kwargs.get("nodes")
        elsets: Elsets = kwargs.get("elsets")

        if nodes is None or elsets is None:
            raise ValueError("ColumnsParse requires both 'nodes' and 'elsets' collections")

        return cls._parse_column(raw_line, tokens, nodes, elsets)

    # ----------------------------------------------------------
    @classmethod
    def _parse_column(cls, raw_line: str, tokens: List[List[str]], nodes: Nodes, elsets: Elsets) -> Column:
        cls._col_counter += 1
        index = cls._col_counter

        l0 = tokens[0]
        node_index = int(l0[0])
        elset_index = int(l0[1])   # 🔹 was element
        group = int(l0[2])
        alpha = int(l0[3])

        # preserve spacing-sensitive tail text
        misc = raw_line.split(None, 4)[-1] if len(raw_line.split(None, 4)) > 4 else ""

        node = nodes.get(node_index)
        elset = elsets.get(elset_index)

        if node is None:
            raise ValueError(f"Column {index} references missing node {node_index}")
        if elset is None:
            raise ValueError(f"Column {index} references missing elset {elset_index}")

        return Column(
            index=index,
            location=node,
            elset=elset,
            group=group,
            alpha=alpha,
            misc=misc,
        )

    @classmethod
    def from_model(cls, model: Model, nodes: Nodes, elsets: Elsets) -> Columns:
        cls._col_counter = 0
        return super().from_model(model, nodes=nodes, elsets=elsets)

class ColumnsAdapter(ObjectCollectionAdapter[Model, Column, Columns]):

    @classmethod
    def format_line(cls, column: Column) -> str:
        loc = int(column.location.index)
        e = int(column.elset.index)
        g = int(column.group)
        a = int(column.alpha)
        misc = str(column.misc)

        line = f'{loc:>6}  {e:<2} {g:>2} {a} {misc}'
        return line

