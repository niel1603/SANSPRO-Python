import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from SANSPRO.model.model import ModelAdapter

from SANSPRO.output.output import OutputAdapter
from SANSPRO.output._support_reactions import SupportReactionsEngine

from SANSPRO.variable.loading import LoadingParse, LoadingEngine, LoadingAdapter

from SANSPRO.collection.point_loads import PointLoadsAdapter

# Step 1 Create new model with template load combination
# -> Input full_path
#   -> klik kanan file model
#   -> copy path
#   -> paste dalam full_path 
# -> Run python
# -> Run model generated (model_name_LOADCOM.MDL) using SANSPRO

# ==============================
# Input base model path
full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\TIPE 1\TIPE 1_v1_5.MDL"
)
# ==============================

folder_path = str(full_path.parent)
model_name = full_path.stem

output_model_name = f"{model_name}_LOADCOMB"

# Create Model
model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)
model_adapter.to_text(model= model, folder_path=folder_path, model_name=output_model_name)

# Set Load Combination for load case linear equation
loading = LoadingEngine().set_load_combination()
model = LoadingAdapter.to_model(loading, model)

# Merge new Point Loads to model
model_adapter.to_text(model= model, folder_path=folder_path, model_name=output_model_name)