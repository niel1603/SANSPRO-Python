from pathlib import Path

from model.model import ModelAdapter
from output.output import OutputAdapter

from output._support_reactions import SupportReactionsEngine
from variable.loading import LoadingParse, LoadingEngine, LoadingAdapter

from collection.nodes import NodesParse, NodeQuery, NodesEngine, NodesAdapter
from collection.point_loads import PointLoadsParse, PointLoadsAdapter


from util.excel_export import export_multiple_collections_to_excel


# Step 2 : convert reaction to point load
# -> Input full_path
#   -> klik kanan file model
#   -> copy path
#   -> paste dalam full_path 
# -> Run python
# -> Output:
#    -> SANSPRO Model with assigned Point Load
#    -> Excel generated then convert to desired format

# ==============================
# Input base model path
full_path = Path(
    r"F:\DANIEL\1_PROJECTS\G12372_Solo Urbana Bolon\CALCULATION\SANSPRO\L7\SANSPRO_UB L7_3_8.MDL"
)
# ==============================

folder_path = str(full_path.parent)
model_name = full_path.stem

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
output = output_adapter.from_text(folder_path, model_name_loadcomb)

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