import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Union

from model.Model import ModelAdapter
from collection.Nodes import Nodes
from collection.Nodes import NodesParse

from output.SupportReactions import SupportReactions, SupportReactionsParser


@dataclass
class Output:
    path: str
    support_reactions: Dict[int, SupportReactions]

    def get(self, combo_index: int) -> SupportReactions:
        return self.support_reactions.get(combo_index)

    def add(self, combo_index: int, output: SupportReactions) -> None:
        self.support_reactions[combo_index] = output

class OutputAdapter:
    def __init__(self, encoding: str = "utf-8"):
        self.reaction_parser = SupportReactionsParser(encoding)

    def from_text(self, folder_path: Union[str, Path], model_name: str) -> Output:

        folder_path = Path(folder_path)
        output_path = folder_path / f"{model_name}.OUT"

        model_adapter = ModelAdapter(encoding='cp1252')
        model = model_adapter.from_text(folder_path, model_name)

        nodes = NodesParse.from_model(model)

        parsed = self.reaction_parser.parse(nodes, output_path)

        return Output(path=output_path, support_reactions=parsed)
