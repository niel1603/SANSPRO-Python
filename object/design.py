from enum import IntEnum, IntFlag

from dataclasses import dataclass, field
from abc import ABC

from SANSPRO.object.ObjectAbstract import Object

class StructureType(IntEnum):
    DUCTILE = 1
    NON_DUCTILE = 2
    BRACED_FRAME = 3
    WALLED_FRAME = 4

class FunctionIndex(IntEnum):
    GENERAL = 0
    TRUSS = 1
    BEAM = 2
    COLUMN = 3
    SHEAR_WALL = 4
    SLAB = 5
    CABLE_WIRE = 6

class DesignCode(IntEnum):
    CONCRETE_ACI_89 = 5
    CONCRETE_ACI_95 = 6
    CONCRETE_ACI_91 = 7
    CONCRETE_AASHTO_98 = 9
    CONCRETE_ACI_2002 = 10
    CONCRETE_PBI_2003 = 12
    CONCRETE_SNI_2013 = 14
    CONCRETE_ACI_2014 = 16 # SNI_2019

class ColumnRebarFace(IntEnum):
    TWO_FACES = 2
    FOUR_FACES = 4
    
class StirrupType(IntEnum):
    RECTANGLE = 1
    SPIRAL = 2

@dataclass
class DesignBase(Object, ABC):
    type_index: int
    type_name: str
    name: str

    function_index: FunctionIndex
    structure_type: StructureType
    design_code: DesignCode

    compute_k: bool
    show_detail: bool
    show_diagram: bool
    use_global_load_factor: bool

    # phi
    phi_flexure: float
    phit_flex_tens: float
    phi_flex_comp: float
    phi_flex_comp_spiral: float
    phi_shear: float
    phi_torsion: float
    phi_bearing: float
    phi_connection: float

    # length factors
    k_x: float
    k_y: float
    l_u: float #Lu/L
    l_ux: float #Lux/L
    l_uy: float #Luy/L

    # Moment multiplier
    c_mx: float
    c_my: float
    cb: float

    # Live load reduction
    gravity_load_reduction: float
    earthquake_load_reduction: float

    cv: float
    reinforced_concrete: 'ReinforcedConcrete'

@dataclass
class ReinforcedConcrete:
    # Concrete properties
    ec: float
    fc1: float
    fci: float
    fcr: float

    # Main reinforcement
    fy: float
    db: float
    delta: float 
    column_rebar_faces: ColumnRebarFace

    # Side reinforcement
    fys: float
    dbs: float
    nside: float
    sidebar_space: float  

    # Shear reinforcement (stirrups)
    stirrup_types: StirrupType
    fyv: float
    dbv: float
    stirrup_space_max: float

    # Hollow section or composite info
    hollow_section: bool
    tcc: float
    tcf: float

@dataclass
class DesignConcreteSlab(DesignBase):
    tp: float
    
@dataclass
class DesignConcreteWall(DesignBase):
    tp: float

@dataclass
class DesignConcreteGirder(DesignBase):
    bw: float
    ht: float
    bf: float
    tf: float

@dataclass
class DesignConcreteBiaxialColumn(DesignBase):
    b: float
    h: float
    bf: float
    tf: float

@dataclass
class DesignConcreteCircularColumn(DesignBase):
    d: float