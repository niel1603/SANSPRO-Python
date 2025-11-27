from typing import List, Optional, Type

from SANSPRO.model.model import Model
from collection._collection_abstract import Collection, CollectionParser, ObjectCollectionQuery, ObjectCollectionEngine, ObjectCollectionAdapter

from SANSPRO.object.diaphargm import Diaphragm

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
    def match_node_indices(collection: Diaphragms, node_indices: List[int]) -> Diaphragms:
        """
        Force diaphragm indices to match exactly the given node index list.
        Missing ones are created. Extra ones are removed.
        """

        # Current diaphragms mapped by index
        current_map = {d.index: d for d in collection.objects}
        new_objects = []

        for idx in node_indices:
            if idx in current_map:
                # Keep existing, stable reference
                new_objects.append(current_map[idx])
            else:
                # Create minimal diaphragm
                new_objects.append(
                    Diaphragm(
                        index=idx,
                        tower_data=["TOWER 0 0 0"],
                        diaph_data=["DIAPH 0 0 0"],
                    )
                )

        # Replace collection objects entirely
        collection.objects = new_objects
        return collection