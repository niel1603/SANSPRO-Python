from typing import List, Optional, Type

from SANSPRO.model.model import Model
from SANSPRO.object.story import Story
from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter
    )

from SANSPRO.variable.building import BuildingParse, BuildingAdapter
from SANSPRO.variable.parameter import ParameterParse, ParameterAdapter
from SANSPRO.collection.diaphragms import DiaphragmsParse, DiaphragmsEngine, DiaphragmsAdapter

class Stories(Collection[Story]):
    header = 'STOREY'
    item_type = Story
        
class StoriesParse(CollectionParser[Model, Story, Stories]):
    LINES_PER_ITEM = 1

    @classmethod
    def get_collection(cls) -> Type[Stories]:
        return Stories

    @classmethod
    def parse_line(cls, lines: List[str]) -> Story:
        raw_line = lines[0]
        tokens = [line.strip().split() for line in lines]
        return cls._parse_node(tokens, raw_line)

    @staticmethod
    def _parse_node(tokens: List[List[str]], raw_line) -> Story:
        l0 = tokens[0]

        # raw_line = raw_line
        # part1 = raw_line[0:10]    # 0–9
        # part2 = raw_line[10:31]   # 10–30
        # part3 = raw_line[31:32]   # 31
        # part4 = raw_line[32:]     # 32–end

        # use new data, always re-compute earthquake load after write back from this data
        part2 = '               0            0            0            0            0            0            0             0            0             0            0            0            0             0            0 0.00 0.00            0            0                0 0'
        part4= 0

        return Story(
            index=int(l0[0]),
            name=str(l0[1]),
            column_layout=int(l0[2]),
            beam_layout=int(l0[3]),
            shearwall_layout=int(l0[4]),
            rigid=bool(l0[5]),
            height=float(l0[6]),
            live_lrf=float(l0[7]),
            col_axial_lrf=float(l0[8]),
            plate_thick=float(l0[7]),
            misc1=str(part2),
            force_opt=int(l0[31]),
            misc2=int(part4),
        )
    
class StoriesAdapter(ObjectCollectionAdapter[Model, Story, Stories]):

    @classmethod
    def update_var(cls, stories: Stories, model: Model) -> Model:

        building = BuildingParse.from_mdl(model)
        building.storey = len(stories.objects) - 1 # Floor count from 0 
        model = BuildingAdapter.to_model(building, model)
        return model

    @classmethod
    def format_line(cls, s: Story) -> str:
        i = s.index
        n = s.name
        cl = s.column_layout
        bl = s.beam_layout
        sl = s.shearwall_layout
        r = s.rigid
        h = s.height
        l_lrf = s.live_lrf
        c_lrf = s.col_axial_lrf
        pt = s.plate_thick
        m1 = s.misc1
        fo = s.force_opt
        m2 = s.misc2
        return f"   {i}  {n:<11} {cl}  {bl}  {sl} {r} {h:>10} {l_lrf} {c_lrf} {pt} {m1} {fo} {m2}"