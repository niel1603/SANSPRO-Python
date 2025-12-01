import math
from typing import Type, List, Tuple, Optional

from SANSPRO.model.model import Model
from SANSPRO.object.node import Node
from SANSPRO.object.slab import Region
from SANSPRO.collection.nodes import Nodes
from SANSPRO.collection.slabs import Slabs

from SANSPRO.variable.building import BuildingParse, BuildingAdapter

from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)
    

class Regions(Collection[Region]):
    header = "REGION"

class RegionsParse(CollectionParser[Model, Region, Regions]):
    """Parses *REGION* block — flat collection but modeled like a layout parser."""
    LINES_PER_ITEM = 1
    _region_counter: int = 0

    @classmethod
    def get_collection(cls) -> Type[Regions]:
        return Regions

    @classmethod
    def from_model(cls, model: Model, nodes: Nodes, slabs: Slabs) -> Regions:
        block = model.blocks.get(cls.get_collection().header)
        lines = block.body
        regions: list[Region] = []
        cls._region_counter = 0

        for raw_line in lines:
            stripped = raw_line.strip()
            if not stripped:
                continue

            region = cls.parse_line([raw_line], nodes=nodes, slabs=slabs)
            regions.append(region)

        return Regions(regions)

    # ----------------------------------------------------------
    @classmethod
    def parse_line(cls, lines: List[str], **kwargs) -> Region:
        raw_line = lines[0]
        tokens = [raw_line.strip().split()]
        nodes: Nodes = kwargs.get("nodes")
        slabs: Slabs = kwargs.get("slabs")

        if nodes is None or slabs is None:
            raise ValueError("RegionsParse requires both 'nodes' and 'slabs' collections")

        return cls._parse_region(raw_line, tokens, nodes, slabs)

    @classmethod
    def _parse_region(
        cls, raw_line: str, tokens: List[List[str]], nodes: Nodes, slabs: Slabs
    ) -> Region:
        cls._region_counter += 1
        index = cls._region_counter
        l0 = tokens[0]

        floor = int(l0[0])
        slab_index = int(l0[1])
        slab = slabs.get(slab_index)
        option = int(l0[2])
        qDL_add = float(l0[3])

        # ----------------------------------------------------------
        # Explicitly parse 4 edge nodes (always present)

        node1 = nodes.get(int(l0[4].rstrip(",")))
        node2 = nodes.get(int(l0[5].rstrip(",")))
        node3 = nodes.get(int(l0[6].rstrip(",")))
        node4 = nodes.get(int(l0[7].rstrip(",")))
        edges = (node1, node2, node3, node4)

        # ----------------------------------------------------------
        # Parse offset and qLL_add
        # ----------------------------------------------------------
        offset = int(l0[8])
        qLL_add = float(l0[9])

        # ----------------------------------------------------------
        # Preserve everything after qLL_add as misc (full spacing)
        # ----------------------------------------------------------
        misc = raw_line.split(None, 10)[-1]

        return Region(
            index=index,
            floor=floor,
            slab=slab,
            option=option,
            qDL_add=qDL_add,
            qLL_add=qLL_add,
            edges=edges,
            offset=offset,
            misc=misc,
        )

    @staticmethod
    def remap_elsets(regions: Regions):
        """
        Regions reference Slabs, so no direct remap. 
        This function only checks consistency after slab remapping.
        """

        for region in regions.objects:
            if region.slab.elset is None:
                raise ValueError(
                    f"[RegionsParse.remap_elsets] Region {region.index} slab "
                    f"{region.slab.index} has no elset after remapping"
                )

class RegionsEngine(ObjectCollectionEngine[Region, Regions]):
    @classmethod
    def canonicalize_edges(cls, nodes: Tuple[Node, Node, Node, Node]) -> Tuple[Node, Node, Node, Node]:
        """
        Canonicalize region corners to standard order based on coordinates:
        - [0] bottom-left:  min x, min y
        - [1] bottom-right: max x, min y
        - [2] top-right:    max x, max y
        - [3] top-left:     min x, max y
        
        This ordering is based on actual coordinate values, not traversal order.
        """
        # Find bounding box
        min_x = min(n.x for n in nodes)
        max_x = max(n.x for n in nodes)
        min_y = min(n.y for n in nodes)
        max_y = max(n.y for n in nodes)
        
        tol = 1e-6
        
        # Identify each corner by its position
        bottom_left = None
        bottom_right = None
        top_right = None
        top_left = None
        
        for n in nodes:
            if abs(n.x - min_x) < tol and abs(n.y - min_y) < tol:
                bottom_left = n
            elif abs(n.x - max_x) < tol and abs(n.y - min_y) < tol:
                bottom_right = n
            elif abs(n.x - max_x) < tol and abs(n.y - max_y) < tol:
                top_right = n
            elif abs(n.x - min_x) < tol and abs(n.y - max_y) < tol:
                top_left = n
        
        # Ensure all corners were found
        if not all([bottom_left, bottom_right, top_right, top_left]):
            # Fallback to original nodes if not a proper rectangle
            return nodes
        
        return (bottom_left, bottom_right, top_right, top_left)


    
    # --------------------------------------------------
    # Orientation helpers
    # --------------------------------------------------
    @classmethod
    def is_ccw(cls, nodes: Tuple[Node, Node, Node, Node]) -> bool:
        """Check if nodes are in counter-clockwise order using shoelace formula."""
        area = 0.0
        for i in range(4):
            x1, y1 = nodes[i].x, nodes[i].y
            x2, y2 = nodes[(i+1) % 4].x, nodes[(i+1) % 4].y
            area += (x2 - x1) * (y2 + y1)
        return area < 0

    @classmethod
    def ensure_ccw(cls, nodes: Tuple[Node, Node, Node, Node]) -> Tuple[Node, Node, Node, Node]:
        """Ensure region edges are CCW by reversing if needed."""
        return nodes if cls.is_ccw(nodes) else (nodes[0], nodes[3], nodes[2], nodes[1])

    @staticmethod
    def _node_key(n: Node, ndigits: int = 6) -> tuple[float, float, float]:
        """Create a hashable key for a node with rounded coordinates."""
        return (round(n.x, ndigits), round(n.y, ndigits), round(n.z, ndigits))

    # ----------------------------------------------------------------------
    # REPLICATE (grid translation) — base + regions_to_copy
    # ----------------------------------------------------------------------
    
    @staticmethod
    def replicate(
        base_regions: Regions,
        regions_to_copy: Regions,
        *,
        nodes: Nodes,
        nx: int = 0, ny: int = 0, nz: int = 0,
        dx: float = 0.0, dy: float = 0.0, dz: float = 0.0,
        include_original: bool = True,
        tolerance: float = 1e-6,
        debug: bool = False,
    ) -> Regions:
        """
        Replicate geometry of `regions_to_copy` using a 3D grid offset.
        `base_regions` are treated as existing geometry.
        """

        # -----------------------------------------
        # Prepare
        # -----------------------------------------
        base_existing = list(base_regions.objects)
        templates = list(regions_to_copy.objects)

        # Prebuild node lookup
        node_lookup = {}
        for n in nodes.objects:
            key = (
                round(n.x / tolerance) * tolerance,
                round(n.y / tolerance) * tolerance,
                round(n.z / tolerance) * tolerance,
            )
            node_lookup[key] = n

        def find_node(x: float, y: float, z: float):
            key = (
                round(x / tolerance) * tolerance,
                round(y / tolerance) * tolerance,
                round(z / tolerance) * tolerance,
            )
            return node_lookup.get(key)

        # -----------------------------------------
        # Duplicate detection
        # -----------------------------------------
        existing_region_keys = set()
        for r in base_existing:
            node_set = frozenset(RegionsEngine._node_key(n) for n in r.edges)
            existing_region_keys.add((r.floor, node_set))

        def region_exists(floor: int, corners):
            node_set = frozenset(RegionsEngine._node_key(n) for n in corners)
            return (floor, node_set) in existing_region_keys

        # -----------------------------------------
        # New region generation
        # -----------------------------------------
        new_regions = []
        next_index = (
            max((r.index for r in base_existing), default=0)
            + 1
        )

        for tpl in templates:

            cx = [n.x for n in tpl.edges]
            cy = [n.y for n in tpl.edges]
            cz = [n.z for n in tpl.edges]

            for ix in range(nx + 1):
                for iy in range(ny + 1):
                    for iz in range(nz + 1):

                        # Skip the original location
                        if ix == iy == iz == 0:
                            continue

                        # Find all corners
                        new_nodes = []
                        for i in range(4):
                            nxp = cx[i] + ix * dx
                            nyp = cy[i] + iy * dy
                            nzp = cz[i] + iz * dz

                            n = find_node(nxp, nyp, nzp)
                            if n is None:
                                break
                            new_nodes.append(n)

                        if len(new_nodes) != 4:
                            continue

                        corners = tuple(new_nodes)

                        # Skip duplicates
                        if region_exists(tpl.floor, corners):
                            continue

                        # Canonicalize
                        corners = RegionsEngine.canonicalize_edges(corners)

                        # Create region
                        new_region = Region(
                            index=next_index,
                            floor=tpl.floor,
                            slab=tpl.slab,
                            option=tpl.option,
                            qDL_add=tpl.qDL_add,
                            qLL_add=tpl.qLL_add,
                            edges=corners,
                            offset=tpl.offset,
                            misc=tpl.misc,
                        )

                        new_regions.append(new_region)

                        # Mark as existing
                        node_set = frozenset(RegionsEngine._node_key(n) for n in corners)
                        existing_region_keys.add((tpl.floor, node_set))

                        next_index += 1

        # -----------------------------------------
        # Build final output according to semantics
        # -----------------------------------------
        if include_original:
            combined = base_existing + new_regions
        else:
            combined = new_regions

        return Regions(objects=combined)

    # ----------------------------------------------------------------------
    # MIRROR (mirror 4-corner polygon)
    # ----------------------------------------------------------------------
    @staticmethod
    def mirror(
        regions: Regions,
        nodes: Nodes,
        *,
        x1: float, y1: float,
        x2: float, y2: float,
        include_original: bool = True,
        tolerance: float = 1e-6,
        debug: bool = False,
    ) -> Regions:
        """
        Mirror regions across a line defined by two points.

        Args:
            regions: Regions to mirror
            nodes: Available nodes
            x1, y1: First point defining the mirror line
            x2, y2: Second point defining the mirror line
            include_original: If True, include original regions in output
            tolerance: Coordinate comparison tolerance
            debug: Enable debug output

        Returns:
            Mirrored Regions collection
        """
        base = list(regions.objects)

        # Build node lookup dictionary with tolerance-based rounding
        lookup = {
            (round(n.x, 6), round(n.y, 6), round(n.z, 6)): n
            for n in nodes.objects
        }

        # Validate mirror line
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        if L < tolerance:
            raise ValueError(f"Mirror line must not be a point (length={L:.2e})")

        # Normalize mirror line direction
        ux = dx / L
        uy = dy / L

        if debug:
            print(f"[MIRROR] Line from ({x1},{y1}) to ({x2},{y2})")
            print(f"  Length: {L:.3f}, Direction: ({ux:.3f}, {uy:.3f})")

        def mirror_point(px: float, py: float, pz: float) -> tuple[float, float, float]:
            """Mirror a point across the line and normalize to avoid floating-point errors."""
            # Translate point so mirror line passes through origin
            px -= x1
            py -= y1

            # Rotate to align mirror line with x-axis
            rx = ux * px + uy * py
            ry = -uy * px + ux * py

            # Reflect across x-axis (negate y-component)
            ry = -ry

            # Rotate back
            mx = ux * rx - uy * ry
            my = uy * rx + ux * ry

            # Translate back
            mx += x1
            my += y1

            # Normalize to 6 decimal places to match node lookup keys
            # This prevents floating-point errors from causing lookup failures
            mx = round(mx, 6)
            my = round(my, 6)
            mz = round(pz, 6)

            return mx, my, mz

        out = base.copy() if include_original else []
        next_index = max((r.index for r in base), default=0) + 1
        new_regions: List[Region] = []
        skipped = 0

        for r in base:
            mirrored_nodes = []

            for nd in r.edges:
                mx, my, mz = mirror_point(nd.x, nd.y, nd.z)
                # Key is already normalized in mirror_point
                key = (mx, my, mz)
                
                if key not in lookup:
                    if debug:
                        print(f"[SKIP] Region #{r.index}: Missing node at ({mx:.3f}, {my:.3f}, {mz:.3f})")
                    mirrored_nodes = []
                    skipped += 1
                    break
                    
                mirrored_nodes.append(lookup[key])

            if len(mirrored_nodes) != 4:
                continue
            
            # Canonicalize to standard corner order
            mirrored_nodes = RegionsEngine.canonicalize_edges(tuple(mirrored_nodes))

            new_region = Region(
                index=next_index,
                floor=r.floor,
                slab=r.slab,
                option=r.option,
                qDL_add=r.qDL_add,
                qLL_add=r.qLL_add,
                edges=tuple(mirrored_nodes),
                offset=r.offset,
                misc=r.misc
            )
            new_regions.append(new_region)
            next_index += 1

        out.extend(new_regions)

        if debug:
            print(f"\n[MIRROR SUMMARY]")
            print(f"  Input: {len(base)} regions")
            print(f"  Mirrored: {len(new_regions)} regions")
            print(f"  Skipped: {skipped} regions (missing nodes)")
            print(f"  Output: {len(out)} regions")

        return Regions(objects=out)

class RegionsAdapter(ObjectCollectionAdapter[Model, Region, Regions]):

    @classmethod
    def update_var(cls, regions: Regions, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.slab_region = len(regions.objects)
        model = BuildingAdapter.to_model(building, model)

        return model

    @classmethod
    def format_line(cls, r: Region) -> str:
        flr  = int(r.floor)
        slb  = int(r.slab.index)
        opt  = int(r.option)

        qdla = cls._norm_float(r.qDL_add)
        qlla = cls._norm_float(r.qLL_add)

        n1, n2, n3, n4 = r.edges

        e1 = int(n1.index)
        e2 = int(n2.index)
        e3 = int(n3.index)
        e4 = int(n4.index)

        ofs  = int(r.offset)
        msc  = str(r.misc)

        line = f'   {flr}  {slb} {opt} {qdla}  {e1:>2}, {e2:>2}, {e3:>2}, {e4:>2} {ofs} {qlla}  {msc}'
        return line