import numpy as np
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Union

from SANSPRO.object.node import Node
from object.point_load import PointLoad
from collection.point_loads import PointLoads
from SANSPRO.collection.nodes import Nodes

@dataclass
class SupportReaction:
    node: Node
    fx: float
    fy: float
    fz: float
    mx: float
    my: float
    mz: float

@dataclass
class SupportReactions:
    reactions: List[SupportReaction]

class SupportReactionsParser:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def parse(self, nodes: Nodes, source: Union[str, Path]) -> Dict[int, SupportReactions]:
        path = Path(source)
        combo_outputs: Dict[int, SupportReactions] = {}

        combo_index = None
        reading = False
        data: List[SupportReaction] = []

        with open(path, 'r', encoding=self.encoding) as f:
            for line in f:
                stripped = line.strip()

                if stripped.startswith("Loading Combination"):
                    if combo_index is not None:
                        combo_outputs[combo_index] = SupportReactions(reactions=data)
                    combo_index = int(stripped.split(":")[1].strip())
                    data = []
                    reading = False

                elif re.match(r"^Joint\s+Force-X\s+Force-Y\s+Force-Z", stripped):
                    reading = True

                elif "SUM =" in stripped or "---" in stripped:
                    reading = False

                elif reading and stripped:
                    parts = re.split(r"\s+", stripped)
                    if len(parts) == 7:
                        node_idx = int(parts[0])
                        node = nodes.index(node_idx)
                        values = list(map(float, parts[1:]))
                        reaction = SupportReaction(
                            node=node,
                            fx=values[0],
                            fy=values[1],
                            fz=values[2],
                            mx=values[3],
                            my=values[4],
                            mz=values[5],
                        )
                        data.append(reaction)

        if combo_index is not None and data:
            combo_outputs[combo_index] = SupportReactions(reactions=data)

        return combo_outputs

class SupportReactionsEngine:

    @staticmethod
    def convert_to_point_loads(
        combo_factored: Dict[int, List[float]],
        support_reactions_dict: Dict[int, SupportReactions],
        floor: int = 0,
        misc: int = 1,
        blast: int = 0
    ) -> PointLoads:
        """
        Convert support reactions to point loads by solving for individual case reactions.
        """
        components = ["fx", "fy", "fz", "mx", "my", "mz"]
        case_ids = list(range(len(next(iter(combo_factored.values())))))
        combo_ids = sorted(combo_factored.keys())
        
        # Get node mapping once
        node_map = {}
        for reaction in support_reactions_dict[combo_ids[0]].reactions:
            node_map[reaction.node.index] = reaction.node
        
        point_loads = []
        index_counter = 1

        # Process each node
        for node_id, node_obj in node_map.items():
            # Solve for all components of this node across all cases
            node_case_data = {}  # case_id -> {component: value}
            
            for comp in components:
                # Build matrix for this component
                A = []
                b = []
                
                for combo_id in combo_ids:
                    A.append(combo_factored[combo_id])
                    reaction = next(r for r in support_reactions_dict[combo_id].reactions 
                                  if r.node.index == node_id)
                    b.append(getattr(reaction, comp))
                
                # Solve for individual case values
                A = np.array(A)
                b = np.array(b)
                x = np.linalg.lstsq(A, b, rcond=None)[0]
                
                # Store results for each case
                for case_index, value in zip(case_ids, x):
                    if case_index not in node_case_data:
                        node_case_data[case_index] = {}
                    node_case_data[case_index][comp] = value
            
            # Create PointLoad objects directly
            for case_id, components_data in node_case_data.items():
                if all(abs(components_data[comp]) < 1e-8 for comp in components):
                    continue  # skip if all components are zero or near-zero

                pl = PointLoad(
                    index=index_counter,
                    load_case=case_id,
                    floor=floor,
                    node=node_obj,
                    fx=-components_data["fx"],
                    fy=-components_data["fy"],
                    fz=-components_data["fz"],
                    mx=-components_data["mx"],
                    my=-components_data["my"],
                    mz=-components_data["mz"],
                    misc=misc,
                    blast=blast
                )
                point_loads.append(pl)
                index_counter += 1


        return PointLoads(point_loads)