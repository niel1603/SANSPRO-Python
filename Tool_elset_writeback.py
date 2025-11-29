import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from SANSPRO.compact.elset.section_properties import SectionPropertyAdapter
from SANSPRO.collection.elsets import ElsetsAdapter, ElsetMerger

# ==============================
# SINGLE INPUT PATH
# ==============================

input_model = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\TIPE 1\TIPE 1_v1_3.MDL"
)
folder_path = str(input_model.parent)
file_name = input_model.stem
increment_version = 0
increment_sub_version = 1

main_version = file_name.rsplit("_", 1)[0]
model_name = main_version.rsplit("v", 1)[0]
main_version = int(main_version.rsplit("v", 1)[1]) + increment_version
sub_version = int(file_name.rsplit("_", 1)[1]) + increment_sub_version

if increment_version != 0:
    output_filename = f"{model_name}v{main_version}_0"
else:
    output_filename = f"{model_name}v{main_version}_{sub_version}"

input_excel = f"{folder_path}\{file_name}.xlsx" 

# ==============================
# IMPORT FROM EXCEL
# ==============================

adapter = SectionPropertyAdapter()

import_excel_path = input_excel

imported_section_props = adapter.from_excel(import_excel_path)

(imported_elsets,
 imported_materials,
 imported_sections,
 imported_designs,
 ) = ElsetsAdapter.from_section_properties(imported_section_props)

from SANSPRO.model.model import ModelAdapter
from SANSPRO.collection.sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.elsets import ElsetsParse

# ==============================
# LOAD EXISTING MODEL FILE (.MDL)
# ==============================

existing_model_path = input_model
# existing_model_path = Path(
#     r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\A2\A2_v1_2.MDL"
# )

folder_path = str(existing_model_path.parent)
model_name = existing_model_path.stem

model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)

existing_materials = MaterialsParse.from_model(model)
existing_sections = SectionsParse.from_model(model)
existing_designs = DesignsParse.from_model(model, existing_sections)
existing_elsets = ElsetsParse.from_model(model,
                                         materials=existing_materials,
                                         sections=existing_sections,
                                         designs=existing_designs,
                                         )

from SANSPRO.collection.nodes import NodesParse
from SANSPRO.layout.beam_layouts import BeamLayoutsParse
from SANSPRO.layout.column_layouts import ColumnLayoutsParse
from SANSPRO.collection.slabs import SlabsParse
from SANSPRO.layout.regions import RegionsParse

nodes = NodesParse.from_model(model)

beam_layouts = BeamLayoutsParse.from_model(model, nodes, existing_elsets)
beams_used_elsets=beam_layouts.get_used_elsets()

col_layouts = ColumnLayoutsParse.from_model(model, nodes, existing_elsets)
columns_used_elsets=col_layouts.get_used_elsets()

slabs = SlabsParse.from_model(model, existing_elsets)
regions = RegionsParse.from_model(model, nodes, slabs)
slabs_used_elsets=slabs.get_used_elsets()

used_elsets = beams_used_elsets | columns_used_elsets | slabs_used_elsets

# ==============================
# IMPORT NEW ELSET INTO EXISTING MODEL
# ==============================
merger = ElsetMerger(existing_elsets, imported_elsets, used_elsets, existing_materials, imported_materials)

(
    merged_elsets,
    merged_materials,
    merged_sections,
    merged_designs,
    reorder_elset_map
) = merger.merge()

BeamLayoutsParse.remap_elsets(
    beam_layouts=beam_layouts,
    reorder_map=reorder_elset_map,
    new_elsets=merged_elsets,
)

ColumnLayoutsParse.remap_elsets(
    column_layouts=col_layouts,
    reorder_map=reorder_elset_map,
    new_elsets=merged_elsets,
)

SlabsParse.remap_elsets(
    slabs=slabs,
    reorder_map=reorder_elset_map,
    new_elsets=merged_elsets,
)

# ==============================
# WRITE BACK MODEL FILE (OUTPUT .MDL)
# ==============================
from SANSPRO.collection.elsets import ElsetsAdapter
from SANSPRO.collection.materials import MaterialsAdapter
from SANSPRO.collection.sections import SectionsAdapter
from SANSPRO.collection.designs import DesignsAdapter

from SANSPRO.layout.beam_layouts import BeamLayoutsAdapter
from SANSPRO.layout.column_layouts import ColumnLayoutsAdapter
from SANSPRO.collection.slabs import SlabsAdapter
from SANSPRO.layout.regions import  RegionsAdapter

model = ElsetsAdapter.to_model(merged_elsets, model)
model = MaterialsAdapter.to_model(merged_materials, model)
model = SectionsAdapter.to_model(merged_sections, model)
model = DesignsAdapter.to_model(merged_designs, model)
model = BeamLayoutsAdapter.to_model(beam_layouts, model)
model = ColumnLayoutsAdapter.to_model(col_layouts, model)
model = SlabsAdapter.to_model(slabs, model)
model = RegionsAdapter.to_model(regions, model)

model_adapter.to_text(model= model, folder_path=folder_path, model_name=output_filename)