import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from SANSPRO.model.model import ModelAdapter
from SANSPRO.collection.nodes import Nodes, NodesParse, NodesAdapter
from SANSPRO.collection.offsets import Offsets, OffsetsAdapter
from SANSPRO.collection.stories import Stories, StoriesAdapter

from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.elsets import ElsetsParse

from SANSPRO.collection._collection_abstract import ObjectCollectionAdapter
from SANSPRO.compact.layout.beam_layout_compact import BeamCompact, CompactBeamLayout, CompactBeamLayouts
from SANSPRO.compact.layout.column_layout_compact import ColumnCompact, CompactColumnLayout, CompactColumnLayouts

# ==============================
# SINGLE INPUT PATH
# ==============================

input_model = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\KAVLING CARSON\KAVLING CARSON_v1_1.MDL"
)
folder_path = str(input_model.parent)
file_name = input_model.stem
increment_version = 0
increment_sub_version = 2

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
# PARSE MODEL AND ELSET
# ==============================

existing_model_path = input_model
# existing_model_path = Path(
#     r"D:\COMPUTATIONAL\Model\SANSPRO\KAVLING CARSON\KAVLING CARSON_v1_0.MDL"
# )
folder_path = str(existing_model_path.parent)
model_name = existing_model_path.stem

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
nodes = NodesParse.from_model(model)

# -------------------------------------------------------------
# IMPORT BASE GEOMETRY : Nodes, Offset, and Stories
# -------------------------------------------------------------

collections = ObjectCollectionAdapter.from_excel(
    folder_path=folder_path,
    excel_name=model_name,
    mapping={
        "Nodes": Nodes,
        "Offsets": Offsets,
        "Stories": Stories,
    }
)

nodes_imported: Nodes = collections["Nodes"]
offsets_imported: Offsets = collections["Offsets"]
stories_imported: Stories = collections["Stories"]

model = model
model = NodesAdapter.to_model(nodes_imported, model)
model = OffsetsAdapter.to_model(offsets_imported, model)
model = StoriesAdapter.to_model(stories_imported, model)

# -------------------------------------------------------------
# IMPORT HIGH LEVEL GEOMETRY : Beam Layouts and Column Layouts 
# -------------------------------------------------------------

compact_beam_layouts = CompactBeamLayouts.from_excel(
    folder=folder_path,
    excel_name='BeamLayouts',
    layout_cls=CompactBeamLayout,
    item_cls=BeamCompact,
)

beam_layouts = compact_beam_layouts.to_full(
    nodes=nodes_imported,
    elsets=elsets
)

compact_column_layouts = CompactColumnLayouts.from_excel(
    folder=folder_path,
    excel_name='ColumnLayouts',
    layout_cls=CompactColumnLayout,
    item_cls=ColumnCompact,
)

column_layouts = compact_column_layouts.to_full(
    nodes=nodes_imported,
    elsets=elsets
)

from SANSPRO.layout.beam_layout import BeamLayoutsParse, BeamLayoutsAdapter
from SANSPRO.layout.column_layout import ColumnLayoutsParse, ColumnLayoutsAdapter

model = BeamLayoutsAdapter.to_model(beam_layouts, model)
model = ColumnLayoutsAdapter.to_model(column_layouts, model)

model_adapter.to_text(model= model, folder_path=folder_path, model_name=output_filename)