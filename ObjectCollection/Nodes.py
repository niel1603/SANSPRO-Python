from typing import List, Optional, Type

from Model.Model import Model
from Object.Node import Node
from ObjectCollection.CollectionAbstract import Collection, CollectionParser, ObjectCollectionQuery, ObjectCollectionEngine, ObjectCollectionAdapter

from Variable.Building import BuildingParse, BuildingAdapter
from Variable.Parameter import ParameterParse, ParameterAdapter
from ObjectCollection.Diaphragms import DiaphragmsParse, DiaphragmsEngine, DiaphragmsAdapter

class Nodes(Collection[Node]):
    header = 'NODEXY'
        
class NodesParse(CollectionParser[Model, Node, Nodes]):

    @classmethod
    def get_collection(cls) -> Type[Nodes]:
        return Nodes

    @classmethod
    def parse_line(cls, line: str) -> Node:
        parts = line.strip().split()
        return Node(
            index=int(parts[0]),
            x=float(parts[1]),
            y=float(parts[2]),
            z=float(parts[3])
        )
    
class NodesAdapter(ObjectCollectionAdapter[Model, Node, Nodes]):

    @classmethod
    def update_var(cls, nodes: Nodes, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.layout_node = len(nodes.objects)
        model = BuildingAdapter.to_model(building, model)

        parameter = ParameterParse.from_mdl(model)
        parameter.node_2d = len(nodes.objects)
        model = ParameterAdapter.to_model(parameter, model)

        diaphragms = DiaphragmsParse.from_model(model)
        diaphragms = DiaphragmsEngine.extend(diaphragms, len(nodes.objects))
        model = DiaphragmsAdapter.to_model(diaphragms, model)

        return model

    @classmethod
    def format_line(cls, node: Node) -> str:
        x_str = cls.norm_float(node.x)
        y_str = cls.norm_float(node.y)
        z_str = cls.norm_float(node.z)
        return f"   {node.index}  {x_str} {y_str}  {z_str}   "

class NodeQuery(ObjectCollectionQuery[Node, Nodes]):
    @staticmethod
    def get_by_indices(collection: Nodes, indices: List[int]) -> Nodes:
        selected_nodes = [collection.index(i) for i in indices if collection.index(i) is not None]
        result = Nodes(selected_nodes)
        return result

    @staticmethod
    def get_by_offset(collection: Nodes, dx: float, dy: float, dz: float, 
                      origin: Optional[Node] = None) -> Optional[Node]:

        if origin is None:
            origin = min(collection.objects, key=lambda n: (n.x, n.y, n.z))

        target_x = origin.x + dx
        target_y = origin.y + dy
        target_z = origin.z + dz

        tol = 1e-6
        for node in collection.objects:
            if (abs(node.x - target_x) < tol and
                abs(node.y - target_y) < tol and
                abs(node.z - target_z) < tol):
                return node
            
        return None
    
    @staticmethod
    def _is_point_on_segment(px: float, py: float,
                             x1: float, y1: float,
                             x2: float, y2: float,
                             tolerance: float = 1e-8) -> bool:
        cross_product = (py - y1) * (x2 - x1) - (px - x1) * (y2 - y1)
        if abs(cross_product) > tolerance:
            return False
        dot_product = (px - x1) * (px - x2) + (py - y1) * (py - y2)
        return dot_product <= 0
    
    @staticmethod
    def _is_point_inside_polygon(x: float, y: float, polygon: List[tuple]) -> bool:
        inside = False
        n = len(polygon)
        j = n - 1
        for i in range(n):
            xi, yi = polygon[i]
            xj, yj = polygon[j]

            if NodeQuery._is_point_on_segment(x, y, xi, yi, xj, yj):
                return True

            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
                inside = not inside
            j = i
        return inside

    @staticmethod
    def select_by_polygon(collection: Nodes, boundary_indices: List[int]) -> Nodes:
        polygon_nodes = NodeQuery.get_by_indices(collection, boundary_indices)
        polygon_coords = [(node.x, node.y) for node in polygon_nodes.objects]

        if len(polygon_coords) < 3:
            return Nodes([])

        inside_nodes = [
            node for node in collection.objects
            if NodeQuery._is_point_inside_polygon(node.x, node.y, polygon_coords)
        ]

        return Nodes(inside_nodes)

class NodesEngine(ObjectCollectionEngine[Node, Nodes]):

    @staticmethod
    def replicate(base_collection: Nodes,
                  selected_objects: Nodes,
                  nx=1, ny=1, nz=1,
                  dx=0.0, dy=0.0, dz=0.0) -> Nodes:

        tol = 1e-6
        index_counter = max((n.index for n in base_collection.objects), default=0) + 1

        def node_exists(x: float, y: float, z: float) -> bool:
            return any(
                abs(n.x - x) < tol and abs(n.y - y) < tol and abs(n.z - z) < tol
                for n in base_collection.objects
            )

        new_nodes: List[Node] = []

        for node in selected_objects.objects:
            for ix in range(nx):
                for iy in range(ny):
                    for iz in range(nz):
                        if ix == iy == iz == 0:
                            continue

                        new_x = node.x + dx * ix
                        new_y = node.y + dy * iy
                        new_z = node.z + dz * iz

                        if node_exists(new_x, new_y, new_z):
                            continue

                        new_node = Node(
                            index=index_counter,
                            x=new_x,
                            y=new_y,
                            z=new_z
                        )
                        new_nodes.append(new_node)
                        index_counter += 1

        new_nodes.sort(key=lambda n: n.index)
        result_collection = Nodes(objects=base_collection.objects.copy())
        result_collection.extend(new_nodes)

        return result_collection

