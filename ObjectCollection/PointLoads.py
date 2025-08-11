from typing import List, Optional, Type

from Model.Model import Model
from ObjectCollection.Nodes import Nodes, NodesParse
from Object.PointLoad import PointLoad
from ObjectCollection.CollectionAbstract import Collection, CollectionParser, ObjectCollectionQuery, ObjectCollectionEngine, ObjectCollectionAdapter

from Variable.Parameter import ParameterParse, ParameterAdapter

class PointLoads(Collection[PointLoad]):
    header = 'JLOAD'

class PointLoadsParse(CollectionParser[Model, PointLoad, PointLoads]):

    @classmethod
    def get_collection(cls) -> Type[PointLoads]:
        return PointLoads

    @classmethod
    def parse_line(cls, line: str, nodes: Nodes, index: int) -> 'PointLoad':
        parts = line.strip().split()
        fx_to_mz = parts[4].split(',')

        return PointLoad(
            index=index,
            load_case=int(parts[0]),
            floor=int(parts[2]),
            node=nodes.index(int(parts[3])),
            fx=float(fx_to_mz[0]),
            fy=float(fx_to_mz[1]),
            fz=float(fx_to_mz[2]),
            mx=float(fx_to_mz[3]),
            my=float(fx_to_mz[4]),
            mz=float(fx_to_mz[5]),
            misc=int(parts[1]),
            blast=int(parts[5])
        )
    
    @classmethod
    def from_model(cls, model: Model) -> PointLoads:
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)
        parsed_items: List[PointLoad] = []

        nodes = NodesParse.from_model(model)

        for i, line in enumerate(block.body, start=1):
            parsed_item = cls.parse_line(line, nodes, index=i)
            parsed_items.append(parsed_item)

        return collection_cls(parsed_items)

    
class PointLoadsAdapter(ObjectCollectionAdapter[Model, PointLoad, PointLoads]):

    @classmethod
    def update_var(cls, point_loads: PointLoads, model: Model) -> Model:

        parameter = ParameterParse.from_mdl(model)
        parameter.joint_load = len(point_loads.objects)
        model = ParameterAdapter.to_model(parameter, model)

        return model

    @classmethod
    def format_line(cls, point_load: PointLoad) -> str:
        load_case = int(point_load.load_case)

        floor = int(point_load.floor)
        node = int(point_load.node.index)
        fx = cls.norm_float(point_load.fx)
        fy = cls.norm_float(point_load.fy)
        fz = cls.norm_float(point_load.fz)
        mx = cls.norm_float(point_load.mx)
        my = cls.norm_float(point_load.my)
        mz = cls.norm_float(point_load.mz)

        misc = int(point_load.misc)
        blast = int(point_load.blast)
        return f"   {load_case}  {misc}  {floor}   {node}  {fx},{fy},{fz},{mx},{my},{mz}  {blast}"