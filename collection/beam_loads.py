import math
from typing import List, Optional, Type, Set, Tuple, Literal

from SANSPRO.model.model import Model
from SANSPRO.object.node import Node
from SANSPRO.object.beam import Beam
from SANSPRO.object.beam_load import LoadDirectionType, FrameLoadTable, BeamLoad 
from SANSPRO.collection.nodes import Nodes, NodeQuery
from SANSPRO.layout.beam_layout import BeamLayout, BeamLayouts, BeamLayoutsQuery


from SANSPRO.collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter
    )

from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from variable.parameter import ParameterParse, ParameterAdapter

class FrameLoadTables(Collection[FrameLoadTable]):
    header = 'FLOADTAB'
    item_type = FrameLoadTable

class FrameLoadTablesParse(CollectionParser[Model, FrameLoadTable, FrameLoadTables]):

    @classmethod
    def get_collection(cls) -> Type[FrameLoadTables]:
        return FrameLoadTables
    
    @classmethod
    def parse_line(cls, lines: List[str]) -> 'FrameLoadTable':
        line = lines[0].strip()
        parts = line.split()

        q, s1, s2, misc1, misc2 = map(float, parts[2].split(','))

        return FrameLoadTable(
            index= int(parts[0]),
            load_type= LoadDirectionType(int(parts[1])),
            q=q,
            s1=s1,
            s2=s2,
            misc=(int(misc1), int(misc2)),
            note=parts[3]
        )
    
class FrameLoadTablesAdapter(ObjectCollectionAdapter[Model, FrameLoadTable, FrameLoadTables]):

    @classmethod
    def update_var(cls, frame_load_tables: FrameLoadTables, model: Model) -> Model:

        parameter = ParameterParse.from_mdl(model)
        parameter.frame_load_type = len(frame_load_tables.objects)
        model = ParameterAdapter.to_model(parameter, model)

        return model

    @classmethod
    def format_line(cls, frame_load_table: FrameLoadTable) -> str:
        i = int(frame_load_table.index)
        lt = int(frame_load_table.load_type)
        q = cls._norm_float(frame_load_table.q)
        s1 = cls._norm_float(frame_load_table.s1)
        s2 = cls._norm_float(frame_load_table.s2)

        m1 = cls._norm_float(frame_load_table.misc[0])
        m2 = cls._norm_float(frame_load_table.misc[0])

        n = str(frame_load_table.note)

        return f"{i:>5} {lt:>3}  {q},{s1},{s2},{m1},{m2}  {n}"

class BeamLoads(Collection[BeamLoad]):
    header = 'BLOAD'
    item_type = BeamLoad

class BeamLoadsParse(CollectionParser[Model, BeamLoad, BeamLoads]):

    @classmethod
    def get_collection(cls) -> Type[BeamLoads]:
        return BeamLoads

    @classmethod
    def parse_line(cls, line: str, frame_load_tables: FrameLoadTables, index: int) -> 'BeamLoad':
        parts = line.strip().split()

        return BeamLoad(
            index=index,
            load_case= int(parts[0]),
            floor= int(parts[1]),
            beam_id= int(parts[2]),
            load=frame_load_tables.get(int(parts[3]))
        )
    
    @classmethod
    def from_model(cls, model: Model) -> BeamLoads:
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)
        parsed_items: List[BeamLoad] = []

        frame_load_tables = FrameLoadTablesParse.from_model(model)

        for i, line in enumerate(block.body, start=1):
            parsed_item = cls.parse_line(line, frame_load_tables, index=i)
            parsed_items.append(parsed_item)

        return collection_cls(parsed_items)
    
class BeamLoadQuery(ObjectCollectionQuery[BeamLoad, BeamLoads]):

    @staticmethod
    def find_loads_on_beam(loads: BeamLoads, beam_id: int) -> List[BeamLoad]:
        return [bl for bl in loads.objects if bl.beam_id == beam_id]

    @staticmethod
    def clone_with_new_beam(load: BeamLoad, new_beam_id: int) -> BeamLoad:
        return BeamLoad(
            index=load.index,
            load_case=load.load_case,
            floor=load.floor,
            beam_id=new_beam_id,
            load=load.load,
        )

    @staticmethod
    def clone_with_beam(load: BeamLoad, new_beam_id: int, new_index: int = 0) -> BeamLoad:
        return BeamLoad(
            index=new_index,
            load_case=load.load_case,
            floor=load.floor,
            beam_id=new_beam_id,
            load=load.load
        )

    @staticmethod
    def find_loads_for_beam(loads: List[BeamLoad], beam_id: int) -> List[BeamLoad]:
        return [bl for bl in loads if bl.beam_id == beam_id]
    
    @classmethod
    def find_beam_by_nodes_in_floor(cls,
                                    layouts: BeamLayouts,
                                    floor: int,
                                    n1: Node, n2: Node
                                   ) -> Tuple[Optional[Beam], Optional[BeamLayout]]:

        # locate layout by floor/index
        try:
            layout = layouts.get(floor)
        except KeyError:
            return None, None

        # match beam only inside this layout
        for item in layout.items:
            if cls._match_two_node_item(item, n1, n2):
                return item, layout

        return None, None

class BeamLoadEngine(ObjectCollectionEngine[BeamLoad, BeamLoads]):

    # ================================================================
    # INTERNAL: GEOMETRY-BASED KEYS
    # ================================================================
    @staticmethod
    def _geom_key_from_nodes(n1: Node, n2: Node) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        p1 = (round(n1.x, 6), round(n1.y, 6), round(n1.z, 6))
        p2 = (round(n2.x, 6), round(n2.y, 6), round(n2.z, 6))
        # order-independent: start/end swap doesn't matter
        return tuple(sorted((p1, p2)))

    @staticmethod
    def _load_overlap_key(load: BeamLoad, layouts_original: BeamLayouts, layouts_final: BeamLayouts):

        # First try to resolve beam in final layout
        layout_final = layouts_final.get(load.floor)
        beam = None
        if layout_final:
            beam = layout_final.get_item(load.beam_id)

        # If not found → fallback to source (mirrored/original)
        if beam is None:
            layout_orig = layouts_original.get(load.floor)
            if layout_orig:
                beam = layout_orig.get_item(load.beam_id)
                layout = layout_orig
            else:
                return None
        else:
            layout = layout_final

        if beam is None or beam.start is None or beam.end is None:
            return None

        geom = BeamLayoutsQuery.beam_geom_key(beam.start, beam.end)
        return (load.floor, geom, load.load_case)

    # ================================================================
    # INTERNAL: COMBINE WITH POLICY (GEOMETRY-BASED)
    # ================================================================
    @staticmethod
    def _apply_policy_geo(
        *,
        existing: list[BeamLoad],
        new: list[BeamLoad],
        layouts_original: BeamLayouts,   # kept for signature symmetry
        layouts_final: BeamLayouts,
        include_original: bool,
        policy: Literal["skip", "add", "replace"],
    ) -> BeamLoads:

        policy = policy.lower()
        if policy not in {"skip", "add", "replace"}:
            raise ValueError(f"Invalid policy: {policy}")

        # Fast path: only new loads
        if not include_original:
            combined = list(new)
            for i, bl in enumerate(combined, 1):
                bl.index = i
            return BeamLoads(combined)

        def group_by_key(loads: list[BeamLoad], layouts: BeamLayouts) -> dict[tuple, list[BeamLoad]]:
            result: dict[tuple, list[BeamLoad]] = {}
            for ld in loads:
                key = BeamLoadEngine._load_overlap_key(ld, layouts_original, layouts_final)
                if key is None:
                    continue
                result.setdefault(key, []).append(ld)
            return result

        # ✅ Both existing and new are interpreted in the FINAL geometry
        existing_by_key = group_by_key(existing, layouts_final)
        new_by_key      = group_by_key(new,      layouts_final)

        result: list[BeamLoad] = []

        if policy == "skip":
            # keep all existing, add only new loads whose key is not present
            result.extend(existing)
            for key, loads_new in new_by_key.items():
                if key in existing_by_key:
                    continue
                result.extend(loads_new)

        elif policy == "replace":
            # keep only existing loads with non-overlapping key, then add all new
            for key, loads_ex in existing_by_key.items():
                if key not in new_by_key:
                    result.extend(loads_ex)
            for loads_new in new_by_key.values():
                result.extend(loads_new)

        else:  # "add"
            result.extend(existing)
            result.extend(new)

        # reindex
        for i, bl in enumerate(result, 1):
            bl.index = i

        return BeamLoads(result)

    # ================================================================
    # REPLICATE
    # ================================================================
    @staticmethod
    def replicate(
        base_loads: BeamLoads,
        loads_to_copy: BeamLoads,
        *,
        layouts_original: BeamLayouts,
        layouts_final: BeamLayouts,
        nodes: Nodes,
        nx=0, ny=0, nz=0,
        dx=0.0, dy=0.0, dz=0.0,
        include_original=True,
        policy: Literal["skip", "add", "replace"] = "add",
    ) -> BeamLoads:

        existing = list(base_loads.objects)
        new_loads: list[BeamLoad] = []

        for load in loads_to_copy.objects:
            orig_beam = layouts_original.get(load.floor).get_item(load.beam_id)
            if orig_beam is None:
                continue

            n1, n2 = orig_beam.start, orig_beam.end

            for ix in range(nx + 1):
                for iy in range(ny + 1):
                    for iz in range(nz + 1):

                        if ix == iy == iz == 0:
                            continue

                        dx1, dy1, dz1 = ix * dx, iy * dy, iz * dz

                        n1_r = NodeQuery.get_by_offset(nodes, dx1, dy1, dz1, origin=n1)
                        n2_r = NodeQuery.get_by_offset(nodes, dx1, dy1, dz1, origin=n2)
                        
                        if not n1_r or not n2_r:
                            continue

                        # Find replicated beam geometrically
                        new_beam, _ = BeamLayoutsQuery.find_beam_by_nodes_in_floor(
                            layouts_final,
                            floor=load.floor,
                            n1=n1_r,
                            n2=n2_r,
                        )
                        if not new_beam:
                            print(
                                f"[REPLICATE] No replicated beam found "
                                f"for load {load.index} floor={load.floor} "
                                f"orig=({n1.x},{n1.y})-({n2.x},{n2.y}) "
                                f"offset=({dx1},{dy1}) → "
                                f"({n1_r.x},{n1_r.y})-({n2_r.x},{n2_r.y})"
                            )
                            continue

                        # Create replicated load
                        new_loads.append(
                            BeamLoadQuery.clone_with_beam(load, new_beam.index)
                        )

        # Apply geometry-based conflict policy
        return BeamLoadEngine._apply_policy_geo(
            existing=existing,
            new=new_loads,
            layouts_original=layouts_original,
            layouts_final=layouts_final,
            include_original=include_original,
            policy=policy,
        )

    # ================================================================
    # MIRROR
    # ================================================================
    @staticmethod
    def mirror(
        base_loads: BeamLoads,
        *,
        layouts_original: BeamLayouts,
        layouts_final: BeamLayouts,
        nodes: Nodes,
        x1: float, y1: float,
        x2: float, y2: float,
        include_original=True,
        policy: Literal["skip", "add", "replace"] = "add",
    ) -> BeamLoads:

        existing = list(base_loads.objects)

        # Node lookup table
        def nk(n: Node):
            return (round(n.x, 6), round(n.y, 6), round(n.z, 6))

        node_lookup = {nk(n): n for n in nodes.objects}

        # mirror transform
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L < 1e-12:
            raise ValueError("Mirror line cannot be a point")

        ux, uy = dx / L, dy / L
        cos_t, sin_t = ux, uy

        def mirror_point(px, py, pz):
            px -= x1
            py -= y1
            rx =  cos_t * px + sin_t * py
            ry = -sin_t * px + cos_t * py
            ry = -ry
            mx =  cos_t * rx - sin_t * ry + x1
            my =  sin_t * rx + cos_t * ry + y1
            return mx, my, pz

        # Mirror each load
        new_loads = []

        for load in base_loads.objects:
            orig_beam = layouts_original.get(load.floor).get_item(load.beam_id)
            if orig_beam is None:
                continue

            s, e = orig_beam.start, orig_beam.end

            # mirror coordinates
            msx, msy, msz = mirror_point(s.x, s.y, s.z)
            mex, mey, mez = mirror_point(e.x, e.y, e.z)

            key_s = (round(msx, 6), round(msy, 6), round(msz, 6))
            key_e = (round(mex, 6), round(mey, 6), round(mez, 6))

            ns = node_lookup.get(key_s)
            ne = node_lookup.get(key_e)

            if not (ns and ne):
                ns_rev = node_lookup.get(key_e)
                ne_rev = node_lookup.get(key_s)
                if ns_rev and ne_rev:
                    ns, ne = ns_rev, ne_rev
                else:
                    continue

            # lookup mirrored beam geometrically
            new_beam = BeamLayoutsQuery.find_beam_by_xyz(
                layouts_final,
                floor=load.floor,
                sx=ns.x, sy=ns.y, sz=ns.z,
                ex=ne.x, ey=ne.y, ez=ne.z,
            )

            if not new_beam:
                continue

            # clone load
            new_loads.append(
                BeamLoad(
                    index=0,
                    load_case=load.load_case,
                    floor=load.floor,
                    beam_id=new_beam.index,
                    load=load.load,
                )
            )

        # geometry-based conflict resolution
        return BeamLoadEngine._apply_policy_geo(
            existing=existing,
            new=new_loads,
            layouts_original=layouts_original,
            layouts_final=layouts_final,
            include_original=include_original,
            policy=policy,
        )
    
class BeamLoadsAdapter(ObjectCollectionAdapter[Model, BeamLoad, BeamLoads]):

    @classmethod
    def update_var(cls, beam_loads: BeamLoads, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.beam_load = len(beam_loads.objects)
        model = BuildingAdapter.to_model(building, model)

        return model

    @classmethod
    def format_line(cls, beam_load: BeamLoad) -> str:
        lc = int(beam_load.load_case)
        f = int(beam_load.floor)
        b_id = int(beam_load.beam_id)
        l = int(beam_load.load.index)
        return f"   {lc}   {f} {b_id:>3} {l:>3}"