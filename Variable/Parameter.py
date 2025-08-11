from typing import ClassVar, Dict
from dataclasses import dataclass

from Variable.VariableAbstract import Variable, VariableParse, VariableAdapter

@dataclass
class Parameter(Variable):
    node_2d: int
    node_3d: int
    supported_node: int
    material_properties: int
    section_properties: int
    design_data: int
    texture_properties: int
    elset: int
    linear_spring_element: int
    truss_element: int
    frame_element: int
    qps8_element: int
    qpb8_element: int
    quad4_element: int
    nodal_mass: int
    joint_load: int
    truss_load_type: int
    truss_load: int
    frame_load_type: int
    frame_load: int
    material_schedule: int

    key_map: ClassVar[Dict[str, str]] = {
    "node_2d": "Number of 2D Node",
    "node_3d": "Number of 3D Node",
    "supported_node": "Number of Supported Node",
    "material_properties": "Number of Material Properties",
    "section_properties": "Number of Section Properties",
    "design_data": "Number of Design Data",
    "texture_properties": "Number of Texture Properties",
    "elset": "Number of Element Set/ELSET",
    "linear_spring_element": "Number of Linear Spring Element",
    "truss_element": "Number of Truss Element",
    "frame_element": "Number of Frame Element",
    "qps8_element": "Number of QPS8  Element",
    "qpb8_element": "Number of QPB8  Element",
    "quad4_element": "Number of QUAD4 Element",
    "nodal_mass": "Number of Nodal Mass",
    "joint_load": "Number of Joint Load",
    "truss_load_type": "Number of Truss Load Type",
    "truss_load": "Number of Truss Load",
    "frame_load_type": "Number of Frame Load Type",
    "frame_load": "Number of Frame Load",
    "material_schedule": "Number of Material Schedule",
    }

class ParameterParse(VariableParse[Parameter]):
    block_key = "PARAMETER"
    target_cls = Parameter


class ParameterAdapter(VariableAdapter[Parameter]):

    @staticmethod
    def format_line(label: str, value: int) -> str:
        return f"  {label:<30}= {value}"

    block_key = "PARAMETER"
    target_cls = Parameter
