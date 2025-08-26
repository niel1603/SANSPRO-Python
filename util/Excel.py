from openpyxl import Workbook
import os
from typing import List, Tuple

def export_multiple_collections_to_excel(collections: List[Tuple[str, List[object]]],
                                         folder_path: str,
                                         excel_name: str):
    if not collections:
        raise ValueError("No collections provided")

    os.makedirs(folder_path, exist_ok=True)
    filepath = os.path.join(folder_path, f"{excel_name}.xlsx")

    wb = Workbook()
    wb.remove(wb.active)  # remove default sheet

    for sheet_name, objects in collections:
        if not objects:
            continue

        ws = wb.create_sheet(title=sheet_name)
        headers = list(vars(objects[0]).keys())
        ws.append(headers)

        for obj in objects:
            row = []
            for attr_name in headers:
                attr = getattr(obj, attr_name)
                if hasattr(attr, "index"):  # If it's an object with .index
                    row.append(getattr(attr, "index"))
                else:
                    row.append(attr)
            ws.append(row)

    wb.save(filepath)
