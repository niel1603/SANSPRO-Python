import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from SANSPRO.model.model import ModelAdapter
from SANSPRO.collection.nodes import NodesParse, NodeQuery, NodesEngine, NodesAdapter
from SANSPRO.collection.offsets import OffsetsParse
from SANSPRO.collection.stories import StoriesParse
from SANSPRO.collection.slabs import SlabsParse

from SANSPRO.collection.materials import MaterialsParse
from SANSPRO.collection.sections import SectionsParse
from SANSPRO.collection.designs import DesignsParse
from SANSPRO.collection.elsets import ElsetsParse

from SANSPRO.collection.beam_loads import BeamLoadsParse, BeamLoadEngine, BeamLoadsAdapter

from SANSPRO.layout.beam_layout import BeamLayoutsParse, BeamLayoutsEngine, BeamLayoutsAdapter
from SANSPRO.layout.column_layout import ColumnLayoutsParse, ColumnLayoutsEngine, ColumnLayoutsAdapter
from SANSPRO.layout.regions import RegionsParse, RegionsEngine, RegionsAdapter


# ==============================
# SINGLE INPUT PATH
# ==============================

tocopy_model_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\TIPE 1\TIPE 1_v1_8.MDL"
)
tocopy_folder_path = str(tocopy_model_path.parent)
tocopy_file_name = tocopy_model_path.stem
tocopy_increment_version = 0
tocopy_increment_sub_version = 1

tocopy_main_version = tocopy_file_name.rsplit("_", 1)[0]
tocopy_model_name = tocopy_main_version.rsplit("v", 1)[0]
tocopy_main_version = int(tocopy_main_version.rsplit("v", 1)[1]) + tocopy_increment_version
tocopy_sub_version = int(tocopy_file_name.rsplit("_", 1)[1]) + tocopy_increment_sub_version

if tocopy_increment_version != 0:
    tocopy_output_filename = f"{tocopy_model_name}v{tocopy_main_version}_0"
else:
    tocopy_output_filename = f"{tocopy_model_name}v{tocopy_main_version}_{tocopy_sub_version}"

# ==============================
# PARSE BASE MODEL
# ==============================

tocopy_model_adapter = ModelAdapter(encoding='cp1252')
model1 = tocopy_model_adapter.from_text(tocopy_folder_path, tocopy_file_name)

# ==============================
# PARSE ELSET
# ==============================

materials1 = MaterialsParse.from_model(model1)
sections1 = SectionsParse.from_model(model1)
design1 = DesignsParse.from_model(model1, sections1)
elsets1 = ElsetsParse.from_model(model1,
                                         materials=materials1,
                                         sections=sections1,
                                         designs=design1,
                                         )

# ==============================
# IMPORT BASE GEOMETRY : Nodes, Offset, and Stories
# ==============================

nodes1 = NodesParse.from_model(model1)
offsets1 = OffsetsParse.from_model(model1, nodes=nodes1)
slabs1 = SlabsParse.from_model(model1, elsets1)
stories1 = StoriesParse.from_model(model1)

# ==============================
# IMPORT HIGH LEVEL GEOMETRY : Beam Layouts, Column Laouts, Regions 
# ==============================

beam_loads1 = BeamLoadsParse.from_model(model1)

beam_layouts1 = BeamLayoutsParse.from_model(model1, nodes1, elsets1)
column_layouts1 = ColumnLayoutsParse.from_model(model1, nodes1, elsets1)
regions1 = RegionsParse.from_model(model1, nodes1, slabs1)

# MIRROR NODES

x1 = 450/2
y1 = 0
x2 = 450/2
y2 = 1

nodes1_mirrored = NodesEngine.mirror(
    nodes=nodes1, 
    x1=x1, 
    y1=y1, 
    x2=x2, 
    y2=y2,
    include_original=False)

# print(len(nodes1_mirrored.objects))
# for n1 in nodes1_mirrored.objects:
#     print(n1)

# REPLICATE BEAMS
beam_layouts1_mirrored = BeamLayoutsEngine.mirror(
    base_layouts=beam_layouts1,
    layouts_to_mirror=beam_layouts1,   # or selected floors
    nodes=nodes1_mirrored,
    x1=x1, y1=y1,
    x2=x2, y2=y2,
    include_original=False
)

# print('beam layout')
# print(len(beam_layouts1_mirrored.layouts))
# for bl in beam_layouts1_mirrored.layouts:
#     print(f'beam layout {bl.index} : {len(bl.items)}')
#     for b in bl:
#         print(f'beam {b.index}')
#         print(f'start {b.start}')
#         print(f'end {b.end}')


# layout = beam_layouts1_mirrored.get(1)
# print(layout.index)
# beam = layout.get_item(9)
# print(beam)
# # print(beam.index)

# layout = beam_layouts1_mirrored.layouts[0]
# print(layout.index)
# beam = layout.items[8]
# print(beam)
# # print(beam.index)

# REPLICATE COLUMNS
column_layouts1_mirrored = ColumnLayoutsEngine.mirror(
    base_layouts=column_layouts1,
    layouts_to_mirror=column_layouts1,      # or selected floors
    nodes=nodes1_mirrored,
    x1=x1, y1=y1,
    x2=x2, y2=y2,
    include_original=False
)

# layout = column_layouts1_mirrored.get(1)
# print(layout.index)
# beam = layout.get_item(9)
# print(beam)
# # print(beam.index)

# layout = column_layouts1_mirrored.layouts[0]
# print(layout.index)
# beam = layout.items[8]
# print(beam)

regions1_mirrored = RegionsEngine.mirror(
    regions=regions1,
    nodes=nodes1_mirrored,
    x1=x1, y1=y1,
    x2=x2, y2=y2,
    include_original=False
)

# print(f'Region : {len(regions1_mirrored.objects)}')
# for r in regions1_mirrored.objects:
#     print(f'region {r.index}')
#     e1, e2, e3, e4 = r.edges
#     print(f'{e1.index}, {e2.index}, {e3.index}, {e4.index}')

beam_loads1_mirrored = BeamLoadEngine.mirror(
    base_loads=beam_loads1,
    layouts_original=beam_layouts1,
    layouts_final=beam_layouts1_mirrored,
    nodes=nodes1_mirrored,
    x1=x1, y1=y1, x2=x2, y2=y2,
    include_original=False,
    policy="skip",
)

# print(f"Beam loads {len(beam_loads1_mirrored.objects)}")
# for bl in beam_loads1_mirrored.objects:
    
#     print(f"Beam load {bl.index}")
#     print(f"Beam floor {bl.floor}")
#     print(f"Beam index {bl.beam_id}")

#     beam = beam_layouts1_mirrored.get(bl.floor).get_item(bl.beam_id)
#     start = beam.start
#     end = beam.end

#     print(f'start {start}')
#     print(f'end {end}')

# ==============================
# WRITE BACK MODEL FILE (OUTPUT .MDL)
# ==============================

model = NodesAdapter.to_model(nodes1_mirrored, model1)
model = BeamLayoutsAdapter.to_model(beam_layouts1_mirrored, model)
model = ColumnLayoutsAdapter.to_model(column_layouts1_mirrored, model)
model = RegionsAdapter.to_model(regions1_mirrored, model)
model = BeamLoadsAdapter.to_model(beam_loads1_mirrored, model)
tocopy_model_adapter.to_text(model= model, folder_path=tocopy_folder_path, model_name=tocopy_output_filename)

# ==============================
# SINGLE INPUT PATH
# ==============================

base_model_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\TIPE 1\TIPE 1_v1_8.MDL"
)
base_folder_path = str(base_model_path.parent)
base_file_name = base_model_path.stem
base_increment_version = 0
base_increment_sub_version = 1

base_main_version = base_file_name.rsplit("_", 1)[0]
base_model_name = base_main_version.rsplit("v", 1)[0]
base_main_version = int(base_main_version.rsplit("v", 1)[1]) + base_increment_version
base_sub_version = int(base_file_name.rsplit("_", 1)[1]) + base_increment_sub_version

if base_increment_version != 0:
    base_output_filename = f"{base_model_name}v{base_main_version}_0"
else:
    base_output_filename = f"{base_model_name}v{base_main_version}_{base_sub_version}"

# ==============================
# PARSE BASE MODEL
# ==============================

base_model_adapter = ModelAdapter(encoding='cp1252')
model2 = base_model_adapter.from_text(base_folder_path, base_file_name)

# ==============================
# PARSE ELSET
# ==============================

materials2 = MaterialsParse.from_model(model2)
sections2 = SectionsParse.from_model(model2)
design2 = DesignsParse.from_model(model2, sections2)
elsets2 = ElsetsParse.from_model(model2,
                                         materials=materials2,
                                         sections=sections2,
                                         designs=design2,
                                         )

# ==============================
# IMPORT BASE GEOMETRY : Nodes, Offset, and Stories
# ==============================

nodes2 = NodesParse.from_model(model2)
offsets2 = OffsetsParse.from_model(model2, nodes=nodes2)
slabs2 = SlabsParse.from_model(model2, elsets2)
stories2 = StoriesParse.from_model(model2)

# print(len(nodes2.objects))
# for n in nodes2.objects:
#     print(n)


# ==============================
# IMPORT HIGH LEVEL GEOMETRY : Beam Layouts, Column Laouts, Regions 
# ==============================

beam_loads2 = BeamLoadsParse.from_model(model2)

beam_layouts2 = BeamLayoutsParse.from_model(model2, nodes2, elsets2)
column_layouts2 = ColumnLayoutsParse.from_model(model2, nodes2, elsets2)
regions2 = RegionsParse.from_model(model2, nodes2, slabs2)

# print('beam layout')
# print(len(beam_layouts2.layouts))
# for bl in beam_layouts2.layouts:
#     print(f'beam layout {bl.index} : {len(bl.items)}')
#     for b in bl:
#         print(f'beam {b.index}, floor {bl.index}')
#         print(f'start {b.start}')
#         print(f'end {b.end}')

# REPLICATE NODES
nx = 1
ny = 0
nz = 0

dx = 450
dy = 0
dz = 0

nodes = NodesEngine.replicate(
    base_collection=nodes2,
    collection_to_copy=nodes1_mirrored,
    nx=nx,
    ny=ny,
    nz=nz,
    dx=dx,
    dy=dy,
    dz=dz,
)

# print(len(nodes.objects))
# for n in nodes.objects:
#     print(n)

beam_layouts = BeamLayoutsEngine.replicate(
    base_layouts=beam_layouts2,
    layouts_to_copy=beam_layouts1_mirrored,
    nodes=nodes,
    nx=nx, ny=ny, nz=nz,
    dx=dx, dy=dy, dz=dz,
    include_original=True
)

# print('beam layout')
# print(len(beam_layouts.layouts))
# for bl in beam_layouts.layouts:
#     print(f'beam layout {bl.index} : {len(bl.items)}')
#     for b in bl:
#         print(f'beam {b.index}, floor {bl.index}')
#         print(f'start {b.start}')
#         print(f'end {b.end}')

column_layouts = ColumnLayoutsEngine.replicate(
    base_layouts=column_layouts2,
    layouts_to_copy=column_layouts1_mirrored,   # the layouts we want to replicate
    nodes=nodes,
    nx=nx, ny=ny, nz=nz,
    dx=dx, dy=dy, dz=dz,
    include_original=True
)

# print('column layout')
# print(len(column_layouts.layouts))
# for cl in column_layouts.layouts:
#     print(f'column layout {cl.index} : {len(cl.items)}')
#     for c in cl:
#         print(f'column {c.index}')
#         print(f'location {c.location}')

regions = RegionsEngine.replicate(
    base_regions=regions2,
    regions_to_copy=regions1_mirrored,
    nodes=nodes,
    nx=nx, ny=ny, nz=nz,
    dx=dx, dy=dy, dz=dz,
    include_original=True
)

# print(f'Region : {len(regions.objects)}')
# for r in regions.objects:
#     print(f'region {r.index}')
#     e1, e2, e3, e4 = r.edges
#     print(f'{e1}, {e2}, {e3}, {e4}')

beam_loads = BeamLoadEngine.replicate(
    base_loads=beam_loads2,
    loads_to_copy=beam_loads1_mirrored,
    layouts_original=beam_layouts1_mirrored,
    layouts_final=beam_layouts,
    nodes=nodes,
    nx=nx, ny=ny, nz=nz,
    dx=dx, dy=dy, dz=dz,
    include_original=True,
    policy="add",
)

# print(f"Beam loads {len(beam_loads.objects)}")
# for bl in beam_loads.objects:

#     print(f"Beam load {bl.index}")
#     print(f"Beam floor {bl.floor}")
#     print(f"Beam index {bl.beam_id}")

#     beam = beam_layouts.get(bl.floor).get_item(bl.beam_id)
#     start = beam.start
#     end = beam.end

#     print(f'start {start}')
#     print(f'end {end}')

model = NodesAdapter.to_model(nodes, model1)
model = BeamLayoutsAdapter.to_model(beam_layouts, model)
model = ColumnLayoutsAdapter.to_model(column_layouts, model)
model = RegionsAdapter.to_model(regions, model)
model = BeamLoadsAdapter.to_model(beam_loads, model)
base_model_adapter.to_text(model= model, folder_path=base_folder_path, model_name=base_output_filename)
