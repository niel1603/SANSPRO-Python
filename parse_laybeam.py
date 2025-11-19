from pathlib import Path
from model.Model import ModelAdapter
from collection.elsets import ElsetsParse
from collection.Nodes import NodesParse
from collection.beams import BeamLayoutsParse
from collection.columns import ColumnLayoutsParse
from collection.floors import SlabsParse, RegionsParse

full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\ANANDA TERRACE\CLUBHOUSE\CLUB HOUSE_BALAI WARGA_POINT LOAD_CASE COMPLETE SIMPLIFIED_3_0.MDL"
)
folder_path = str(full_path.parent)
model_name = full_path.stem

model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)

elsets = ElsetsParse.from_model(model)

nodes = NodesParse.from_model(model)
# for n in nodes.objects:
#     print(n)

beam_layouts = BeamLayoutsParse.from_model(model, nodes, elsets)
# for layout in beam_layouts.objects:
#     print(f"Layout #{layout.index}, Total={layout.total_beams}, Parsed={len(layout.beams)}")
#     for beam in layout.beams:
#         print(f"  [{beam.index}] {beam.start.index} → {beam.end.index} (elset={beam.elset})")

beams_used_elsets=beam_layouts.get_used_elsets()
print(beams_used_elsets)


col_layouts = ColumnLayoutsParse.from_model(model, nodes, elsets)
# for layout in col_layouts.objects:
#     print(f"Layout #{layout.index}, Total={layout.total_columns}, Parsed={len(layout.columns)}")
#     for col in layout.columns:
#         print(f"  [{col.index}] Node {col.location.index} → Elset={col.elset}, Group={col.group}, Alpha={col.alpha}")

columns_used_elsets=col_layouts.get_used_elsets()
print(columns_used_elsets)



slabs = SlabsParse.from_model(model, elsets)
regions = RegionsParse.from_model(model, nodes, slabs)
# for region in regions.objects:
#     print(
#         f"Region {region.index} | Floor={region.floor}, Slab={region.slab.name}, Elset={region.slab.elset}, "
#         f"Edges={[n.index for n in region.edges]} | misc='{region.misc[:20]}...'"
#     )

slabs_used_elsets=slabs.get_used_elsets()
print(slabs_used_elsets)
