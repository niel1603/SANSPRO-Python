import math
from typing import Type, List

from SANSPRO.model.model import Model
from SANSPRO.object.node import Node
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
    
class ColumnsEngine(ObjectCollectionEngine[Column, Columns]):

    @staticmethod
    def replicate(
        columns: Columns,
        nodes: Nodes,
        existing_columns: list[Column],
        nx=0, ny=0, nz=0,
        dx=0.0, dy=0.0, dz=0.0,
        include_original=True,
        tol: float = 1e-6
    ) -> Columns:

        base_cols = columns.objects
        all_nodes = nodes.objects

        # Duplicate checker: existing + optionally base
        check_cols = list(existing_columns)
        if include_original:
            check_cols.extend(base_cols)

        next_index = max((c.index for c in check_cols), default=0) + 1
        new_cols: list[Column] = []

        # ---- node finder ----
        def find_node(x, y, z):
            for n in all_nodes:
                if (
                    abs(n.x - x) < tol and
                    abs(n.y - y) < tol and
                    abs(n.z - z) < tol
                ):
                    return n
            return None

        # ---- exists check ----
        def col_exists(nloc):
            for c in check_cols:
                lc = c.location
                if (
                    abs(lc.x - nloc.x) < tol and
                    abs(lc.y - nloc.y) < tol and
                    abs(lc.z - nloc.z) < tol
                ):
                    return True
            return False

        # ---- replicate ----
        for c in base_cols:
            x, y, z = c.location.x, c.location.y, c.location.z

            for ix in range(nx+1):
                for iy in range(ny+1):
                    for iz in range(nz+1):

                        if ix == iy == iz == 0:
                            continue

                        xx = x + ix*dx
                        yy = y + iy*dy
                        zz = z + iz*dz

                        nloc = find_node(xx, yy, zz)
                        if nloc is None:
                            continue

                        if col_exists(nloc):
                            continue

                        new_c = Column(
                            index=next_index,
                            location=nloc,
                            elset=c.elset,
                            group=c.group,
                            alpha=c.alpha,
                            misc=c.misc,
                        )

                        new_cols.append(new_c)
                        check_cols.append(new_c)
                        next_index += 1

        return Columns(objects=new_cols)

    @staticmethod
    def mirror(columns: Columns,
               nodes: Nodes,
               x1: float, y1: float,
               x2: float, y2: float,
               include_original=True) -> Columns:

        tol = 1e-6

        # Node lookup table
        node_lookup = {
            (round(n.x,6), round(n.y,6), round(n.z,6)): n
            for n in nodes.objects
        }

        def mirror_point(px, py, pz):
            dx = x2 - x1
            dy = y2 - y1
            L = math.hypot(dx, dy)
            if L < 1e-12:
                raise ValueError("Mirror line cannot be a point.")
            ux, uy = dx/L, dy/L

            old_px, old_py = px - x1, py - y1

            rx =  ux*old_px + uy*old_py
            ry = -uy*old_px + ux*old_py
            ry = -ry   # reflect

            mx =  ux*rx - uy*ry + x1
            my =  uy*rx + ux*ry + y1

            return mx, my, pz

        base = columns.objects
        out = base.copy() if include_original else []

        next_index = max((c.index for c in base), default=0) + 1
        new_cols: List[Column] = []

        for c in base:
            mx, my, mz = mirror_point(c.location.x, c.location.y, c.location.z)
            key = (round(mx,6), round(my,6), round(mz,6))
            if key not in node_lookup:
                continue

            new_cols.append(Column(
                index=next_index,
                location=node_lookup[key],
                elset=c.elset,
                group=c.group,
                alpha=c.alpha,
                misc=c.misc
            ))
            next_index += 1

        out.extend(new_cols)
        return Columns(objects=out)

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

