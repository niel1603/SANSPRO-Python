from dataclasses import dataclass
from typing import Protocol
from pathlib import Path
import yaml


@dataclass(frozen=True)
class SteelRecord:
    name: str
    function: str
    seismic: bool
    fu: float
    fy: float
    fv: float
    ry: float
    rt: float
    notes: str


class SteelGradeProto(Protocol):
    ST37: SteelRecord
    ST41: SteelRecord
    SS400: SteelRecord


class SteelGrade:
    _all: dict[str, SteelRecord] = {}

    @classmethod
    def load(cls, filename="steel_grades.yaml") -> None:
        # Resolve SANSPRO/docs/steel_grades.yaml
        san_spro_root = Path(__file__).resolve().parents[3]
        path = san_spro_root / "docs" / "dbs" / filename

        data = yaml.safe_load(path.read_text())

        for name, fields in data.items():
            rec = SteelRecord(name=name, **fields)
            cls._all[name] = rec
            setattr(cls, name, rec)

    @classmethod
    def get(cls, name: str) -> SteelRecord:
        return cls._all[name]


