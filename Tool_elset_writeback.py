import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from SANSPRO.collection.section_properties import SectionPropertyAdapter
from SANSPRO.collection.elsets import ElsetsAdapter, ElsetMerger


adapter = SectionPropertyAdapter()

import_excel_path = r"D:\COMPUTATIONAL\Model\SANSPRO\ANANDA TERRACE\CLUBHOUSE\CLUB HOUSE_BALAI WARGA_POINT LOAD_CASE COMPLETE SIMPLIFIED_3_2.xlsx"

imported_section_props = adapter.from_excel(import_excel_path)

(imported_elsets,
 imported_materials,
 imported_sections,
 imported_designs,
 ) = ElsetsAdapter.from_section_properties(imported_section_props)

from pathlib import Path
from model.Model import ModelAdapter
from SANSPRO.collection.Sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.elsets import ElsetsParse

# ==============================
# MODEL
# ==============================

full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\ANANDA TERRACE\CLUBHOUSE\CLUB HOUSE_BALAI WARGA_POINT LOAD_CASE COMPLETE SIMPLIFIED_3_2.MDL"
)
folder_path = str(full_path.parent)
model_name = full_path.stem

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

from SANSPRO.collection.Nodes import NodesParse
from SANSPRO.collection.beams import BeamLayoutsParse
from SANSPRO.collection.columns import ColumnLayoutsParse
from SANSPRO.collection.floors import SlabsParse, RegionsParse

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
# MERGE
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
# TO MODEL
# ==============================
from SANSPRO.collection.elsets import ElsetsAdapter
from SANSPRO.collection.materials import MaterialsAdapter
from SANSPRO.collection.Sections import SectionsAdapter
from SANSPRO.collection.designs import DesignsAdapter

from SANSPRO.collection.beams import BeamLayoutsAdapter
from SANSPRO.collection.columns import ColumnLayoutsAdapter
from SANSPRO.collection.floors import SlabsAdapter, RegionsAdapter

# WRITEBACK
# A. ELSET
model = ElsetsAdapter.to_model(merged_elsets, model)

# A.1. Material
# mm_s = MaterialsAdapter.to_string(merged_materials)
model = MaterialsAdapter.to_model(merged_materials, model)

# A.2. Section 
# ms_s = SectionsAdapter.to_string(merged_sections)
model = SectionsAdapter.to_model(merged_sections, model)

# A.3. Design
# md_s = DesignsAdapter.to_string(merged_designs)
model = DesignsAdapter.to_model(merged_designs, model)

# B. LAYOUT

# B.1. Laybeam
# bl_s = BeamLayoutsAdapter.to_string(beam_layouts)
model = BeamLayoutsAdapter.to_model(beam_layouts, model)

# B.2. Laycol
# cl_s = ColumnLayoutsAdapter.to_string(col_layouts)
model = ColumnLayoutsAdapter.to_model(col_layouts, model)

# B.3. Slab & Region
# s_s = SlabsAdapter.to_string(slabs)
# r_s = RegionsAdapter.to_string(regions)
model = SlabsAdapter.to_model(slabs, model)
model = RegionsAdapter.to_model(regions, model)

output_model_name = f"{model_name}"
model_adapter.to_text(model= model, folder_path=folder_path, model_name=output_model_name)