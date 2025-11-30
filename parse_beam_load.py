import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path

from SANSPRO.model.model import ModelAdapter

from SANSPRO.collection.beam_loads import BeamLoadsParse, BeamLoadsAdapter

full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\RUKO\TIPE 1\TIPE 1_v1_5.MDL"
)
folder_path = str(full_path.parent)
model_name = full_path.stem

model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)

# beam_loads = BeamLoadsParse.from_model(model)

# # for bl in beam_loads:
# #     print(bl)

# beam_loads_str = BeamLoadsAdapter.to_string(beam_loads)
# print(beam_loads_str)

from SANSPRO.collection.point_loads import PointLoadsParse, PointLoadsAdapter

point_loads = PointLoadsParse.from_model(model)

# for pl in point_loads:
#     print(pl)

point_loads_str = PointLoadsAdapter.to_string(point_loads)

print(point_loads_str)