import re
from abc import ABC, abstractmethod
from dataclasses import fields
from typing import Dict, TypeVar, Type, Generic

from Model.Model import Block, Model, BlockAdapter

T = TypeVar("T", bound="Variable")


class Variable(ABC):
    key_map: Dict[str, str] = {}


class VariableParse(ABC, Generic[T]):
    block_key: str
    target_cls: Type[T]

    @classmethod
    def from_mdl(cls, model: Model) -> T:
        block = model.blocks.get(cls.block_key)
        parsed_values = {}
        key_to_field = {v: k for k, v in cls.target_cls.key_map.items()}
        pattern = re.compile(r"^(.*?)\s*=\s*(-?\d+)$")

        for line in block.body:
            match = pattern.match(line.strip())
            if match:
                key, val = match.groups()
                field = key_to_field.get(key.strip())
                if field:
                    parsed_values[field] = int(val)

        return cls.target_cls(**{f.name: parsed_values.get(f.name, 0) for f in fields(cls.target_cls)})


class VariableAdapter(ABC, Generic[T]):
    block_key: str
    target_cls: Type[T]

    @staticmethod
    @abstractmethod
    def format_line(label: str, value: int) -> str:
        pass

    @classmethod
    def to_string(cls, instance: T) -> str:
        lines = [f"*{cls.block_key}*"]
        for field, label in cls.target_cls.key_map.items():
            value = getattr(instance, field, 0)
            lines.append(cls.format_line(label, value))
        return "\n".join(lines)

    @classmethod
    def to_block(cls, instance: T) -> Block:
        lines = []
        for field, label in cls.target_cls.key_map.items():
            value = getattr(instance, field, 0)
            lines.append(cls.format_line(label, value))
        return BlockAdapter.from_lines(header=cls.block_key, lines=lines)
    
    @classmethod
    def to_model(cls, instance: T, model: Model) -> str:
        lines = []
        for field, label in cls.target_cls.key_map.items():
            value = getattr(instance, field, 0)
            lines.append(cls.format_line(label, value))
            
        block = BlockAdapter.from_lines(header=cls.block_key, lines=lines)
        model.blocks[cls.block_key] = block
        return model