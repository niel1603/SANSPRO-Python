from Model.Model import ModelAdapter
from ObjectCollection.Nodes import NodesParse, NodeQuery, NodesEngine, NodesAdapter
from ObjectCollection.PointLoads import PointLoadsParse

from Adapter.Excel import export_multiple_collections_to_excel

# Create adapter
adapter = ModelAdapter(encoding='cp1252')

# Read model (equivalent to your original ReadModel.read_model)
folder_path = "./data/SANSPRO_UB L7_v3"
model_name = "SANSPRO_UB L7_v3_FOUNDATION DESIGN"

excel_name = "SANSPRO_UB L7_v3_FOUNDATION DESIGN"


# Replicate NodeXY's nodes 
model = adapter.from_text(folder_path, model_name)

nodes = NodesParse.from_model(model)
point_loads = PointLoadsParse.from_model(model)

export_multiple_collections_to_excel(
    collections=[
        ("Nodes", nodes.objects),
        ("PointLoads", point_loads.objects)
    ],
    folder_path="./data/SANSPRO_UB L7_v3",
    excel_name="SANSPRO_UB L7_v3_FOUNDATION DESIGN"
)


