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
# TO COPY
# ==============================

tocopy_folder_path = "D:\COMPUTATIONAL\Model\SANSPRO\RUKO"


# ==============================
# BASE MODEL
# ==============================

base_model_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\BLOK A_v1_0.MDL"
)

base_folder_path = str(base_model_path.parent)
base_file_name = base_model_path.stem      # "BLOK A_v1_0"

# Extract main & sub version
base_main = base_file_name.rsplit("_", 1)[0]  # BLOK A_v1
base_sub  = int(base_file_name.rsplit("_", 1)[1])  # 0


# ==============================
# MIRROR & COPY PARAM
# ==============================

x1 = 450/2
y1 = 0
x2 = 450/2
y2 = 1

nx = 1
ny = 0
nz = 0
dx = 450
dy = 0
dz = 0

step_dx = 450
step_dy = 0
step_dz = 0

# ==============================
# RUKO ARRAY
# ==============================

# type_array = ['TIPE 1', 'TIPE 1', 'TIPE 2', 'TIPE 2', 'TIPE 1', 'TIPE 1', 'TIPE 2', 'TIPE 2', 'TIPE 2', 'TIPE 2', 'TIPE 1', 'TIPE 1', 'TIPE 2', 'TIPE 2', 'TIPE 3']
# mirror_array = ['M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M']

type_array = ['TIPE 1', 'TIPE 1', 'TIPE 2', 'TIPE 2', 'TIPE 1', 'TIPE 1', 'TIPE 2', 'TIPE 2', 'TIPE 3']
mirror_array = ['M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M', 'N', 'M']


first_iteration = True

for type, mirror in zip(type_array, mirror_array):

    # ==============================
    # IMPORT TOCOPY
    # ==============================

    tocopy_file_name = type
    tocopy_model_adapter = ModelAdapter(encoding='cp1252')
    model1 = tocopy_model_adapter.from_text(tocopy_folder_path, tocopy_file_name)

    materials1 = MaterialsParse.from_model(model1)
    sections1 = SectionsParse.from_model(model1)
    design1 = DesignsParse.from_model(model1, sections1)
    elsets1 = ElsetsParse.from_model(model1,
                                            materials=materials1,
                                            sections=sections1,
                                            designs=design1,
                                            )

    nodes1 = NodesParse.from_model(model1)
    offsets1 = OffsetsParse.from_model(model1, nodes=nodes1)
    slabs1 = SlabsParse.from_model(model1, elsets1)
    stories1 = StoriesParse.from_model(model1)

    beam_loads1 = BeamLoadsParse.from_model(model1)
    beam_layouts1 = BeamLayoutsParse.from_model(model1, nodes1, elsets1)
    column_layouts1 = ColumnLayoutsParse.from_model(model1, nodes1, elsets1)
    regions1 = RegionsParse.from_model(model1, nodes1, slabs1)

    # ==============================
    # IMPORT BASE
    # ==============================

    if mirror == 'M':

        nodes1_mirrored = NodesEngine.mirror(
            nodes=nodes1, 
            x1=x1, 
            y1=y1, 
            x2=x2, 
            y2=y2,
            include_original=False)

        beam_layouts1_mirrored = BeamLayoutsEngine.mirror(
            base_layouts=beam_layouts1,
            layouts_to_mirror=beam_layouts1,
            nodes=nodes1_mirrored,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
            include_original=False
        )

        column_layouts1_mirrored = ColumnLayoutsEngine.mirror(
            base_layouts=column_layouts1,
            layouts_to_mirror=column_layouts1,
            nodes=nodes1_mirrored,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
            include_original=False
        )

        regions1_mirrored = RegionsEngine.mirror(
            regions=regions1,
            nodes=nodes1_mirrored,
            x1=x1, y1=y1,
            x2=x2, y2=y2,
            include_original=False
        )

        beam_loads1_mirrored = BeamLoadEngine.mirror(
            base_loads=beam_loads1,
            layouts_original=beam_layouts1,
            layouts_final=beam_layouts1_mirrored,
            nodes=nodes1_mirrored,
            x1=x1, y1=y1, x2=x2, y2=y2,
            include_original=False,
            policy="skip",
        )

        nodes1 = nodes1_mirrored
        beam_layouts1 = beam_layouts1_mirrored
        column_layouts1 = column_layouts1_mirrored
        regions1 = regions1_mirrored
        beam_loads1 = beam_loads1_mirrored


    # ==============================
    # COPY INTO BASE
    # ==============================

    base_model_adapter = ModelAdapter(encoding='cp1252')
    model2 = base_model_adapter.from_text(base_folder_path, base_file_name)

    materials2 = MaterialsParse.from_model(model2)
    sections2 = SectionsParse.from_model(model2)
    design2 = DesignsParse.from_model(model2, sections2)
    elsets2 = ElsetsParse.from_model(model2,
                                            materials=materials2,
                                            sections=sections2,
                                            designs=design2,
                                            )

    nodes2 = NodesParse.from_model(model2)
    offsets2 = OffsetsParse.from_model(model2, nodes=nodes2)
    slabs2 = SlabsParse.from_model(model2, elsets2)
    stories2 = StoriesParse.from_model(model2)

    beam_loads2 = BeamLoadsParse.from_model(model2)
    beam_layouts2 = BeamLayoutsParse.from_model(model2, nodes2, elsets2)
    column_layouts2 = ColumnLayoutsParse.from_model(model2, nodes2, elsets2)
    regions2 = RegionsParse.from_model(model2, nodes2, slabs2)


    for b_l in beam_loads2:
        if b_l.load == None:
            print(base_file_name)
            print(b_l.index)
            print(b_l.load_case)
            beam = beam_layouts2.get(b_l.floor).get_item(b_l.beam_id)
            print(f'beam = {beam.index}')
            print(f'start = {beam.start}')
            print(f'end = {beam.end}')


    nodes = NodesEngine.replicate(
        base_collection=nodes2,
        collection_to_copy=nodes1,
        nx=nx,
        ny=ny,
        nz=nz,
        dx=dx,
        dy=dy,
        dz=dz,
    )

    beam_layouts = BeamLayoutsEngine.replicate(
        base_layouts=beam_layouts2,
        layouts_to_copy=beam_layouts1,
        nodes=nodes,
        nx=nx, ny=ny, nz=nz,
        dx=dx, dy=dy, dz=dz,
        include_original=True
    )

    column_layouts = ColumnLayoutsEngine.replicate(
        base_layouts=column_layouts2,
        layouts_to_copy=column_layouts1,
        nodes=nodes,
        nx=nx, ny=ny, nz=nz,
        dx=dx, dy=dy, dz=dz,
        include_original=True
    )

    regions = RegionsEngine.replicate(
        base_regions=regions2,
        regions_to_copy=regions1,
        nodes=nodes,
        nx=nx, ny=ny, nz=nz,
        dx=dx, dy=dy, dz=dz,
        include_original=True
    )

    beam_loads = BeamLoadEngine.replicate(
        base_loads=beam_loads2,
        loads_to_copy=beam_loads1,
        layouts_original=beam_layouts1,
        layouts_final=beam_layouts,
        nodes=nodes,
        nx=nx, ny=ny, nz=nz,
        dx=dx, dy=dy, dz=dz,
        include_original=True,
        policy="skip",
    )

    # for b_l in beam_loads:
    #     if b_l.load == None:
    #         print(b_l.index)

    # print("Before replicate:")
    # for bl in beam_loads1.objects:
    #     if bl.load is None:
    #         print("loads_to_copy has missing load:", bl.index)

    # print("Base loads:")
    # for bl in beam_loads2.objects:
    #     if bl.load is None:
    #         print("base_loads has missing load:", bl.index)

    if first_iteration:
        # bump version once
        base_sub += 1
        base_output_filename = f"{base_main}_{base_sub}"   # BLOK A_v1_1

        first_iteration = False
    else:
        # no more version bumps
        base_output_filename = f"{base_main}_{base_sub}"   # still BLOK A_v1_1


    model = NodesAdapter.to_model(nodes, model1)
    model = BeamLayoutsAdapter.to_model(beam_layouts, model)
    model = ColumnLayoutsAdapter.to_model(column_layouts, model)
    model = RegionsAdapter.to_model(regions, model)
    model = BeamLoadsAdapter.to_model(beam_loads, model)
    base_model_adapter.to_text(model= model, folder_path=base_folder_path, model_name=base_output_filename)

    # next iteration reads the same file
    base_file_name = base_output_filename

    # increment translation offsets
    dx += step_dx
    dy += step_dy
    dz += step_dz