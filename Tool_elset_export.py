import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from SANSPRO.model.model import ModelAdapter
from SANSPRO.collection.sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.elsets import ElsetsParse
from SANSPRO.compact.elset.section_properties import SectionPropertyAdapter
from SANSPRO.util.excel_export import export_multiple_collections_to_excel, strip_prefix_dict_keys

# ==============================
# SINGLE INPUT PATH
# ==============================

full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\A2\A2_v1_1.MDL"
)
folder_path = str(full_path.parent)
model_name = full_path.stem
output_model_name = f"{model_name}"

# ==============================
# PARSE MODEL AND ELSET
# ==============================

# Create Model
model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)

materials = MaterialsParse.from_model(model)
sections = SectionsParse.from_model(model)
designs = DesignsParse.from_model(model, sections)

elsets = ElsetsParse.from_model(model, 
                                materials=materials,
                                sections=sections,
                                designs=designs,
                                )

adapter = SectionPropertyAdapter(materials, sections, designs)
section_properties = adapter.from_elsets(elsets)

# ==============================
# EXPORT TO EXCEL
# ==============================

split = section_properties.split_by_class()

collections = [
    (class_name.replace("SectionProperty", ""), subset.objects)
    for class_name, subset in split.items()
]

collections = [
    (name, subset.objects)
    for name, subset in strip_prefix_dict_keys(split, "SectionProperty").items()
]

export_multiple_collections_to_excel(
    collections=collections,
    folder_path=folder_path,
    excel_name=output_model_name,
)