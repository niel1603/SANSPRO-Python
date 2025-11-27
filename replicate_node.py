from model.model import ModelAdapter
from collection.nodes import NodesParse, NodeQuery, NodesEngine, NodesAdapter

# Input
# Number
nx = 2
ny = 1
nz = 1

# Direction
dx = 850
dy = 0
dz = 0

# Create adapter
adapter = ModelAdapter(encoding='cp1252')

# Read model (equivalent to your original ReadModel.read_model)
folder_path = "./data/SANSPRO_UB L7_v2"
model_name = "SANSPRO_UB L7_v1"

output_path = "./data/IZE Gili Trawangan_Building_1_0_output.MDL"

model = adapter.from_text(folder_path, model_name)

# Replicate NodeXY's nodes 
nodes = NodesParse.from_model(model)

boundary_indices = [1, 3, 6, 5, 8, 7]

nodes_selected = NodeQuery.select_by_polygon(collection=nodes, boundary_indices=boundary_indices)
nodes = NodesEngine.replicate(nodes, nodes_selected, nx, ny, nz, dx, dy, dz)
model = NodesAdapter.to_model(nodes, model)


adapter.to_text(model= model, output_path= output_path)