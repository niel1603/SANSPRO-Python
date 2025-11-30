from typing import List, Optional, Type

from SANSPRO.model.model import Model
from SANSPRO.object.beam_load import LoadDirectionType, FrameLoadTable, BeamLoad 

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