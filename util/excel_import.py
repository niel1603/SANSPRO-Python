import os
from dataclasses import fields, is_dataclass
from enum import Enum
from openpyxl import load_workbook
from typing import Any, Dict, List, Tuple, Type


def _set_nested(data: dict, path: str, value: Any):
    """Rebuild nested structure from dot-separated keys."""
    keys = path.split(".")
    cur = data
    for k in keys[:-1]:
        cur = cur.setdefault(k, {})
    cur[keys[-1]] = value


def _coerce_value(value: str) -> Any:
    """Try to infer numeric/bool/empty types."""
    if value == "" or value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, str):
        val = value.strip()
        # bool
        if val.lower() in ("true", "false"):
            return val.lower() == "true"
        # int
        try:
            if "." not in val:
                return int(val)
        except ValueError:
            pass
        # float
        try:
            return float(val)
        except ValueError:
            pass
    return value


def _expand_nested(flat_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Expand flattened dict into nested dict structure."""
    nested = {}
    for key, val in flat_dict.items():
        _set_nested(nested, key, val)
    return nested


def _dict_to_dataclass(cls: Type, data: Dict[str, Any]):
    """Instantiate dataclass (recursively) from dict."""
    if not is_dataclass(cls):
        raise TypeError(f"{cls} is not a dataclass")

    kwargs = {}
    for f in fields(cls):
        val = data.get(f.name)
        if val is None:
            kwargs[f.name] = None
            continue

        # nested dataclass
        if is_dataclass(f.type) and isinstance(val, dict):
            kwargs[f.name] = _dict_to_dataclass(f.type, val)
        # Enum
        elif isinstance(f.type, type) and issubclass(f.type, Enum):
            try:
                kwargs[f.name] = f.type[val]
            except KeyError:
                kwargs[f.name] = None
        else:
            kwargs[f.name] = _coerce_value(val)
    return cls(**kwargs)


def import_multiple_collections_from_excel(
    filepath: str,
    sheet_to_class: Dict[str, Type],
) -> Dict[str, List[object]]:
    """
    Read Excel file and rebuild collections.

    Args:
        filepath: path to Excel file
        sheet_to_class: mapping {sheet_name: dataclass_type}
    Returns:
        dict: {sheet_name: [objects]}
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(filepath)

    wb = load_workbook(filepath, data_only=True)
    results = {}

    for sheet_name, cls in sheet_to_class.items():
        if sheet_name not in wb.sheetnames:
            continue

        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue

        headers = rows[0]
        objects = []

        for row in rows[1:]:
            flat = {h: _coerce_value(v) for h, v in zip(headers, row)}
            nested = _expand_nested(flat)
            obj = _dict_to_dataclass(cls, nested)
            objects.append(obj)

        results[sheet_name] = objects

    return results

def add_prefix_dict_keys(data: dict, prefix: str) -> dict:
    """Return a new dict with all keys prefixed."""
    return {f"{prefix}{k}": v for k, v in data.items()}