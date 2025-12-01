import math
from typing import Type, List, Optional

from SANSPRO.model.model import Model
from SANSPRO.object.node import Node
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

class BeamsQuery(ObjectCollectionQuery[Beam, Beams]):
    TOL = 1e-6

    # ------------------------------------------------------------
    # Basic queries
    # ------------------------------------------------------------
    @staticmethod
    def get_by_index(beams: Beams, index: int) -> Optional[Beam]:
        return beams.get(index)

    @staticmethod
    def filter_by_floor(beams: Beams, floor: int) -> Beams:
        return Beams([b for b in beams.objects if b.floor == floor])

    @staticmethod
    def connected_to_node(beams: Beams, node: Node) -> Beams:
        tol = BeamsQuery.TOL
        return Beams([
            b for b in beams.objects
            if (abs(b.start.x - node.x) < tol and abs(b.start.y - node.y) < tol and abs(b.start.z - node.z) < tol) or
               (abs(b.end.x   - node.x) < tol and abs(b.end.y   - node.y) < tol and abs(b.end.z   - node.z) < tol)
        ])

    # ------------------------------------------------------------
    # Geometric matching
    # ------------------------------------------------------------
    @staticmethod
    def _match_nodes(a: Node, b: Node, tol: float) -> bool:
        return (
            abs(a.x - b.x) < tol and
            abs(a.y - b.y) < tol and
            abs(a.z - b.z) < tol
        )

    @classmethod
    def find_by_nodes(cls, beams: Beams, n1: Node, n2: Node) -> Optional[Beam]:
        tol = cls.TOL

        for b in beams.objects:
            if (cls._match_nodes(b.start, n1, tol) and cls._match_nodes(b.end, n2, tol)) or \
               (cls._match_nodes(b.start, n2, tol) and cls._match_nodes(b.end, n1, tol)):
                return b

        return None

    # ------------------------------------------------------------
    # Spatial filtering
    # ------------------------------------------------------------
    @staticmethod
    def in_bbox(beams: Beams,
                xmin: float, xmax: float,
                ymin: float, ymax: float) -> Beams:
        result = []
        for b in beams.objects:
            xs = [b.start.x, b.end.x]
            ys = [b.start.y, b.end.y]
            if any(xmin <= x <= xmax and ymin <= y <= ymax for x, y in zip(xs, ys)):
                result.append(b)
        return Beams(result)
    
    
class BeamsEngine(ObjectCollectionEngine[Beam, Beams]):
            
    @staticmethod
    def replicate(
        beams: Beams,
        nodes: Nodes,
        existing_beams: list[Beam],
        nx: int = 0, ny: int = 0, nz: int = 0,
        dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
        include_original: bool = True,
    ) -> Beams:
        """
        Replicate *beams* geometrically into the node grid.

        - `nodes` is the canonical node collection (truth).
        - `existing_beams` = beams already present in target layout.
        - Returns ONLY new beams (indices = 0, will be reindexed later).
        """

        tol = 1e-6
        base_beams = beams.objects

        # Node lookup on coords
        node_lookup: dict[tuple[float, float, float], Node] = {
            (round(n.x, 6), round(n.y, 6), round(n.z, 6)): n
            for n in nodes.objects
        }

        # Geometry-based duplicate check list
        check_beams: list[Beam] = list(existing_beams)
        if include_original:
            check_beams.extend(base_beams)

        def exists_geom(ns: Node, ne: Node) -> bool:
            for b in check_beams:
                s, e = b.start, b.end
                if s is None or e is None:
                    continue

                # normal
                if (abs(s.x - ns.x) < tol and abs(s.y - ns.y) < tol and abs(s.z - ns.z) < tol and
                    abs(e.x - ne.x) < tol and abs(e.y - ne.y) < tol and abs(e.z - ne.z) < tol):
                    return True

                # reversed
                if (abs(s.x - ne.x) < tol and abs(s.y - ne.y) < tol and abs(s.z - ne.z) < tol and
                    abs(e.x - ns.x) < tol and abs(e.y - ns.y) < tol and abs(e.z - ns.z) < tol):
                    return True

            return False

        new_beams: list[Beam] = []

        # -----------------------------
        # Replicate each base beam
        # -----------------------------
        for b in base_beams:
            if b.start is None or b.end is None:
                continue

            sx, sy, sz = b.start.x, b.start.y, b.start.z
            ex, ey, ez = b.end.x, b.end.y, b.end.z

            for ix in range(nx + 1):
                for iy in range(ny + 1):
                    for iz in range(nz + 1):

                        if ix == iy == iz == 0:
                            continue

                        offx = ix * dx
                        offy = iy * dy
                        offz = iz * dz

                        nsx, nsy, nsz = sx + offx, sy + offy, sz + offz
                        nex, ney, nez = ex + offx, ey + offy, ez + offz

                        key_s = (round(nsx, 6), round(nsy, 6), round(nsz, 6))
                        key_e = (round(nex, 6), round(ney, 6), round(nez, 6))

                        ns = node_lookup.get(key_s)
                        ne = node_lookup.get(key_e)

                        if not ns or not ne:

                            continue

                        if exists_geom(ns, ne):
                            continue

                        new_beam = Beam(
                            index=0,  # reindexed by LayoutEngine
                            start=ns,
                            end=ne,
                            elset=b.elset,
                            group=b.group,
                            beam_type=b.beam_type,
                            misc=b.misc,
                        )
                        new_beams.append(new_beam)
                        check_beams.append(new_beam)

        return Beams(objects=new_beams)
    
    @staticmethod
    def mirror(beams: Beams,
               nodes: Nodes,
               x1: float, y1: float,
               x2: float, y2: float,
               include_original: bool = True
               ) -> Beams:
        """
        Mirror beams across line (x1, y1) → (x2, y2).
        Nodes are NOT created here — mirrored beams must map
        to already-existing mirrored nodes.

        include_original=True  → original + mirrored beams
        include_original=False → mirrored only
        """

        base_beams = beams.objects
        tol = 1e-6

        # --------------------------------------
        # Build node lookup table by coordinates
        # --------------------------------------
        node_lookup = {}
        for n in nodes.objects:
            key = (round(n.x, 6), round(n.y, 6), round(n.z, 6))
            node_lookup[key] = n

        

        # Start output list
        result_list = base_beams.copy() if include_original else []

        # Next beam index
        next_index = max((b.index for b in base_beams), default=0) + 1
        new_beams: list[Beam] = []

        # --------------------------------------
        # Prepare mirror math (same as nodes)
        # --------------------------------------
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-12:
            raise ValueError("Mirror line cannot be a single point.")

        ux = dx / L
        uy = dy / L
        cos_t = ux
        sin_t = uy

        def mirror_point(px, py, pz):
            # 1) translate to line origin
            px -= x1
            py -= y1

            # 2) rotate so mirror line aligns with x-axis
            rx =  cos_t * px + sin_t * py
            ry = -sin_t * px + cos_t * py

            # 3) reflect across x-axis
            ry = -ry

            # 4) rotate back
            mx =  cos_t * rx - sin_t * ry
            my =  sin_t * rx + cos_t * ry

            # 5) translate back
            mx += x1
            my += y1

            return mx, my, pz

        # --------------------------------------
        # Mirror beams
        # --------------------------------------
        for b in base_beams:

            # Mirror start
            msx, msy, msz = mirror_point(b.start.x, b.start.y, b.start.z)
            key_s = (round(msx, 6), round(msy, 6), round(msz, 6))

            # Mirror end
            mex, mey, mez = mirror_point(b.end.x, b.end.y, b.end.z)
            key_e = (round(mex, 6), round(mey, 6), round(mez, 6))

            # Node existence check
            if key_s not in node_lookup or key_e not in node_lookup:
                # If target nodes do not exist → cannot mirror this beam
                continue

            new_beams.append(Beam(
                index=next_index,
                start=node_lookup[key_s],
                end=node_lookup[key_e],
                elset=b.elset,
                group=b.group,
                beam_type=b.beam_type,
                misc=b.misc
            ))

            next_index += 1

        result_list.extend(new_beams)
        return Beams(objects=result_list)

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