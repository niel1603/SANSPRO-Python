
from pathlib import Path
from model.Model import ModelAdapter
from collection.Sections import SectionsParse
from collection.designs import DesignsParse
from collection.materials import MaterialsParse
from collection.elsets import ElsetsParse
from collection.elsets import ElsetsAdapter

full_path = Path(
    r"D:\COMPUTATIONAL\Model\SANSPRO\ANANDA TERRACE\CLUBHOUSE\CLUB HOUSE_BALAI WARGA_POINT LOAD_CASE COMPLETE SIMPLIFIED_3_0.MDL"
)
folder_path = str(full_path.parent)
model_name = full_path.stem

model_adapter = ModelAdapter(encoding='cp1252')
model = model_adapter.from_text(folder_path, model_name)

materials = MaterialsParse.from_model(model)

sections = SectionsParse.from_model(model)

designs = DesignsParse.from_model(model, sections)

elsets = ElsetsParse.from_model(
    model,
    materials=materials,
    sections=sections,
    designs=designs,
)

existing_elsets_string = ElsetsAdapter.to_string(elsets)
print('existing_elsets_string:')
print(existing_elsets_string)
