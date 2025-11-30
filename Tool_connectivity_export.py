import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from SANSPRO.model.model import ModelAdapter
from SANSPRO.collection.nodes import NodesParse
from SANSPRO.collection.offsets import OffsetsParse
from SANSPRO.collection.stories import StoriesParse
from SANSPRO.collection.slabs import SlabsParse

from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.elsets import ElsetsParse

from SANSPRO.layout.beam_layout import BeamLayoutsParse
from SANSPRO.layout.column_layout import ColumnLayoutsParse
from SANSPRO.layout.regions import RegionsParse

from SANSPRO.collection._collection_abstract import ObjectCollectionAdapter
from SANSPRO.compact.layout.beam_layout_compact import CompactBeamLayouts
from SANSPRO.compact.layout.column_layout_compact import CompactColumnLayouts
from SANSPRO.compact.layout.region_layout_compact import CompactRegionLayouts

existing_model_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\TIPE 1\TIPE 1_v1_4.MDL"
)
folder_path = str(existing_model_path.parent)
model_name = existing_model_path.stem

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
slabs = SlabsParse.from_model(model, elsets)
stories = StoriesParse.from_model(model)

ObjectCollectionAdapter.export_to_excel(
    collections=[
        ("Nodes", nodes),
        ("Offsets", offsets),
        ("Stories", stories),
        ("Slabs", slabs),
    ],
    folder_path=folder_path,
    excel_name=model_name,
)

beam_layouts = BeamLayoutsParse.from_model(model, nodes, elsets)
column_layouts = ColumnLayoutsParse.from_model(model, nodes, elsets)
region_layouts = RegionsParse.from_model(model, nodes, slabs)

compact_beam_layouts = CompactBeamLayouts.from_layouts(beam_layouts)
compact_column_layouts = CompactColumnLayouts.from_layouts(column_layouts)
compact_region_layouts = CompactRegionLayouts.from_layouts(region_layouts)

compact_beam_layouts.export_to_excel(
    folder=folder_path,
    excel_name='BeamLayouts'
)

compact_column_layouts.export_to_excel(
    folder=folder_path,
    excel_name='ColumnLayouts'
)
compact_region_layouts.export_to_excel(
    folder=folder_path,
    excel_name='Regions'
)