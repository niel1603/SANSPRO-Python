from Model.Model import ModelAdapter
from Output.Output import OutputAdapter

from Output.SupportReactions import SupportReactionsEngine
from Variable.Loading import LoadingParse, LoadingEngine, LoadingAdapter

from ObjectCollection.Nodes import NodesParse, NodeQuery, NodesEngine, NodesAdapter
from ObjectCollection.PointLoads import PointLoadsParse, PointLoadsAdapter


from Adapter.Excel import export_multiple_collections_to_excel


# Step 2 : convert reaction to point load
# -> Input
# -> Run python
# -> Output:
#    -> SANSPRO Model with assigned Point Load
#    -> Excel generated then convert to desired format

# ==============================
# Input 
folder_path = "./data/SANSPRO_UB L7_v3"
model_name = "SANSPRO_UB L7_v3"
# ==============================

model_name_loadcomb = f"{model_name}_LOADCOMB"
output_model_name = f"{model_name}_POINTLOAD"

# Create adapter
adapter = ModelAdapter(encoding='cp1252')

# Replicate NodeXY's nodes 
model = adapter.from_text(folder_path, model_name_loadcomb)

nodes = NodesParse.from_model(model)

# Read output
loading = LoadingParse.from_mdl(model)
output_adapter = OutputAdapter(encoding='cp1252')
output = output_adapter.from_text(folder_path, model_name)

# Convert to Point Loads
point_loads = SupportReactionsEngine.convert_to_point_loads(loading.combo_factored, output.support_reactions)
model = PointLoadsAdapter.to_model(point_loads, model)

# Merge new Point Loads to model
adapter.to_text(model= model, folder_path=folder_path, model_name=output_model_name)

export_multiple_collections_to_excel(
    collections=[
        ("Nodes", nodes.objects),
        ("PointLoads", point_loads.objects)
    ],
    folder_path=folder_path,
    excel_name=output_model_name
)