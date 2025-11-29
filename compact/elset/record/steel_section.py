from dataclasses import dataclass
from typing import Protocol, Dict
from pathlib import Path
import yaml
import re

@dataclass(frozen=True)
class SteelSectionBase:
    name: str
    bw: float
    d: float
    tw: float
    tf: float


@dataclass(frozen=True)
class WideFlangeRecord(SteelSectionBase):
    weight: float
    A: float
    Ix: float
    Iy: float
    Wx: float
    Wy: float
    ix: float
    iy: float


@dataclass(frozen=True)
class BuiltUpWFRecord(SteelSectionBase):
    weight: float
    A: float
    Ix: float
    Iy: float
    Wx: float
    Wy: float
    ix: float
    iy: float

@dataclass(frozen=True)
class LightChannelRecord(SteelSectionBase):
    weight: float
    A: float
    Ix: float
    Iy: float
    Wx: float
    Wy: float
    ix: float
    iy: float
    ex: float

@dataclass(frozen=True)
class HollowBoxRecord(SteelSectionBase):
    weight: float
    A: float
    Ix: float
    Iy: float
    Wx: float
    Wy: float
    ix: float
    iy: float


class SteelSectionProto(Protocol):
    WF: Dict[str, WideFlangeRecord]
    WB: Dict[str, BuiltUpWFRecord]
    C: Dict[str, LightChannelRecord]
    B:  Dict[str, HollowBoxRecord]

class SteelSection(SteelSectionProto):
    WF: Dict[str, WideFlangeRecord] = {}
    WB: Dict[str, BuiltUpWFRecord] = {}
    C: Dict[str, LightChannelRecord] = {}
    B:  Dict[str, HollowBoxRecord] = {}

    _all: Dict[str, SteelSectionBase] = {}
    _yaml_loaded: set[str] = set()
    _dbs_loaded: set[str] = set()

    CLASS_MAP = {
        "WF": WideFlangeRecord,
        "WB": BuiltUpWFRecord,
        "C": LightChannelRecord,
        "B":  HollowBoxRecord,
    }

    FIELD_MAP = {
        "WF": ["name","bw","d","tw","tf","weight","A","Ix","Iy","Wx","Wy","ix","iy"],
        "WB": ["name","bw","d","tw","tf","weight","A","Ix","Iy","Wx","Wy","ix","iy"],
        "C": ["name","bw","d","tw","tf","weight","A","Ix","Iy","Wx","Wy","ix","iy","ex"],
        "B":  ["name","bw","d","tw","tf","weight","A","Ix","Iy","Wx","Wy","ix","iy"],
    }

    # ----------------------------------------------------------------------
    # YAML LOADER
    # ----------------------------------------------------------------------
    @classmethod
    def load_yaml(cls, filename="steel_section.yaml") -> None:
        root = Path(__file__).resolve().parents[3]
        path = root / "docs" / "dbs" / filename

        data = yaml.safe_load(path.read_text())

        for tag, sections in data.items():
            if tag not in cls.CLASS_MAP:
                continue

            rec_class = cls.CLASS_MAP[tag]
            family = getattr(cls, tag)

            for name, fields in sections.items():
                rec = rec_class(name=name, **fields)
                family[name] = rec
                cls._all[name] = rec
                cls._yaml_loaded.add(name)

    # ----------------------------------------------------------------------
    # DBS LOADER (unchanged from last version)
    # ----------------------------------------------------------------------
    @classmethod
    def load_dbs(cls, filename="steel_section.dbs") -> None:
        root = Path(__file__).resolve().parents[3]
        path = root / "docs" / "dbs" / filename

        current_tag = None

        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("{"):
                continue

            if line.startswith("[") and "]" in line:
                tag = line[1:line.index("]")]
                current_tag = tag if tag in cls.CLASS_MAP else None
                continue

            if current_tag is None or line.startswith("{"):
                continue

            tokens = re.split(r"\s+", line)
            fields = cls.FIELD_MAP[current_tag]
            rec_class = cls.CLASS_MAP[current_tag]

            if len(tokens) < len(fields):
                continue

            data = {}
            for f, t in zip(fields, tokens):
                data[f] = t if f == "name" else float(t)

            rec = rec_class(**data)

            family = getattr(cls, current_tag)
            family[rec.name] = rec
            cls._all[rec.name] = rec
            cls._dbs_loaded.add(rec.name)


    # ----------------------------------------------------------------------
    @classmethod
    def get(cls, name: str) -> SteelSectionBase:
        return cls._all[name]
    
    @classmethod
    def exists_in_yaml(cls, name: str) -> bool:
        return name in cls._yaml_loaded


    @classmethod
    def exists_in_dbs(cls, name: str) -> bool:
        return name in cls._dbs_loaded


    @classmethod
    def exists(cls, name: str, source: str = "any") -> bool:
        if source == "any":
            return name in cls._yaml_loaded or name in cls._dbs_loaded
        elif source == "yaml":
            return name in cls._yaml_loaded
        elif source == "dbs":
            return name in cls._dbs_loaded
        else:
            raise ValueError(f"Invalid source {source!r}. Use 'any', 'yaml', or 'dbs'.")
