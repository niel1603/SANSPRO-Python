import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from model.model import ModelAdapter
from SANSPRO.collection.nodes import NodesParse
from SANSPRO.collection.offsets import OffsetsParse
from SANSPRO.collection.stories import StoriesParse

from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.elsets import ElsetsParse

from SANSPRO.layout.beam_layout import BeamLayoutsParse
from SANSPRO.layout.column_layout import ColumnLayoutsParse

from SANSPRO.collection._collection_abstract import ObjectCollectionAdapter
from SANSPRO.compact.layout.beam_layout_compact import CompactBeamLayouts
from SANSPRO.compact.layout.column_layout_compact import CompactColumnLayouts

full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\MTJ\RF1_v2_0\RF1_v2_1.MDL"
)
folder_path = str(full_path.parent)
model_name = full_path.stem

model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)

# Create Model
materials = MaterialsParse.from_model(model)
sections = SectionsParse.from_model(model)
designs = DesignsParse.from_model(model, sections)
elsets = ElsetsParse.from_model(model,
                                         materials=materials,
                                         sections=sections,
                                         designs=designs,
                                         )

nodes = NodesParse.from_model(model)
offsets = OffsetsParse.from_model(model, nodes=nodes)
stories = StoriesParse.from_model(model)

ObjectCollectionAdapter.export_to_excel(
    collections=[
        ("Nodes", nodes),
        ("Offsets", offsets),
        ("Stories", stories),
    ],
    folder_path=folder_path,
    excel_name=model_name,
)

beam_layouts = BeamLayoutsParse.from_model(model, nodes, elsets)
column_layouts = ColumnLayoutsParse.from_model(model, nodes, elsets)

compact_beam_layouts = CompactBeamLayouts.from_layouts(beam_layouts)
compact_column_layouts = CompactColumnLayouts.from_layouts(column_layouts)

compact_beam_layouts.export_to_excel(
    folder=folder_path,
    excel_name='BeamLayouts'
)

compact_column_layouts.export_to_excel(
    folder=folder_path,
    excel_name='ColumnLayouts'
)