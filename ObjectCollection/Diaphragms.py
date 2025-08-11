from typing import List, Optional, Type

from Model.Model import Model
from ObjectCollection.CollectionAbstract import Collection, CollectionParser, ObjectCollectionQuery, ObjectCollectionEngine, ObjectCollectionAdapter

from Object.Diaphargm import Diaphragm

class Diaphragms(Collection[Diaphragm]):
    header = 'MDIAPHTAB'

class DiaphragmsParse(CollectionParser[Model, Diaphragm, Diaphragms]):

    @classmethod
    def get_collection(cls) -> Type['Diaphragms']:
        return Diaphragms

    @classmethod
    def parse_line(cls, tower_line: str, diaph_line: str) -> 'Diaphragm':
        t_parts = tower_line.strip().split()
        d_parts = diaph_line.strip().split()

        index = int(t_parts[0])

        return Diaphragm(
            index=index,
            tower_data=[" ".join(t_parts[1:])],
            diaph_data=[" ".join(d_parts[1:])]
        )

    @classmethod
    def from_model(cls, model: Model) -> Diaphragms:
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)
        lines = block.body
        parsed_items: List[Diaphragm] = []

        i = 0
        while i < len(lines) - 1:
            tower_line = lines[i]
            diaph_line = lines[i + 1]
            parsed_items.append(cls.parse_line(tower_line, diaph_line))
            i += 2

        return collection_cls(parsed_items)
    
class DiaphragmsAdapter(ObjectCollectionAdapter[Model, Diaphragm, Diaphragms]):
    
    @classmethod
    def format_line(cls, obj: Diaphragm) -> str:
        tower_line = f"{obj.index} {obj.tower_data[0]}"
        diaph_line = f"{obj.index} {obj.diaph_data[0]}"
        return f"{tower_line}\n{diaph_line}"
    
class DiaphragmsEngine(ObjectCollectionEngine[Diaphragm, Diaphragms]):
    
    @staticmethod
    def extend(collection: Diaphragms, target_index: int) -> Diaphragms:
        existing_indices = {d.index for d in collection.objects}
        max_existing = max(existing_indices) if existing_indices else 0

        new_objects = []
        for i in range(max_existing + 1, target_index + 1):
            tower_data = [f"TOWER 0 0 0 0"]
            diaph_data = [f"DIAPH 0 0 0 0"]
            new_objects.append(Diaphragm(index=i, tower_data=tower_data, diaph_data=diaph_data))

        collection.extend(new_objects)
        return collection