from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Union

@dataclass
class Block:
    header: str
    body: List[str] = field(default_factory=list)

@dataclass
class Model:
    path: str
    blocks: Dict[str, Block] = field(default_factory=dict)
    encoding: str = "utf-8"

def parse_block_header(line: str) -> Optional[str]:
    stripped = line.strip()
    if stripped.startswith('*') and stripped.endswith('*') and len(stripped) > 2:
        return stripped[1:-1]
    return None

class ModelAdapter:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    def from_text(self, folder_path: Union[str, Path], model_name: str) -> Model:
        folder_path = Path(folder_path)
        path = folder_path / f"{model_name}.MDL"

        blocks = {}
        current_block = None
        current_lines = []

        with open(path, 'r', encoding=self.encoding) as f:
            blocks = OrderedDict()
            current_block = None
            current_lines = []
            in_description = False

            for line in f:
                # Detect start of DESCRIPTION
                if "<DESCRIPTION>" in line:
                    # Save previous block if it exists
                    if current_block:
                        blocks[current_block] = Block(header=current_block, body=current_lines)
                        current_block, current_lines = None, []

                    in_description = True
                    current_block = "DESCRIPTION"
                    current_lines = [line.rstrip()]  # include <DESCRIPTION>
                    continue

                # Inside DESCRIPTION block
                if in_description:
                    current_lines.append(line.rstrip())
                    if "<END>" in line:
                        blocks[current_block] = Block(header=current_block, body=current_lines)
                        current_block, current_lines = None, []
                        in_description = False
                    continue

                # Normal block header
                header = parse_block_header(line)
                if header:
                    # Save previous block
                    if current_block:
                        blocks[current_block] = Block(header=current_block, body=current_lines)
                    current_block = header
                    current_lines = []
                elif line.strip():
                    current_lines.append(line.rstrip())

            # Save last block if needed
            if current_block and current_block not in blocks:
                blocks[current_block] = Block(header=current_block, body=current_lines)

        return Model(path=str(path), blocks=blocks, encoding=self.encoding)

    def to_text(self, model: Model, folder_path: Union[str, Path], model_name: str) -> None:
        folder_path = Path(folder_path)
        path = folder_path / f"{model_name}.MDL"

        block_texts = []

        for block in model.blocks.values():
            if block.header == "DESCRIPTION":
                # 5 blank lines before DESCRIPTION content
                block_text = ("\n" * 5) + "\n".join(block.body)
            else:
                if block.body:
                    block_text = f"*{block.header}*\n" + "\n".join(block.body)
                else:
                    block_text = f"*{block.header}*"
            block_texts.append(block_text)

        text = "\n".join(block_texts).strip() + "\n"
        Path(path).write_text(text, encoding=self.encoding)

class BlockAdapter:
    def __init__(self, encoding: str = "utf-8"):
        self.encoding = encoding

    @staticmethod
    def from_lines(header: str, lines: List[str]) -> Block:

        body = [line.rstrip() for line in lines if line.strip()]
        
        return Block(header=header, body=body)

    def from_text(self, block_path: Union[str, Path]) -> Block:
        path = Path(block_path)
        with open(path, "r", encoding=self.encoding) as f:
            lines = f.readlines()

        header = parse_block_header(lines[0])

        body = [line.rstrip() for line in lines[1:] if line.strip()]
        return Block(header=header, body=body)

    def to_text(self, block: Block, path: Union[str, Path]) -> None:
        lines = [f"*{block.header}*"] + block.body
        text = "\n".join(lines) + "\n"
        Path(path).write_text(text, encoding=self.encoding)
