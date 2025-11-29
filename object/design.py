from enum import IntEnum, IntFlag

from dataclasses import dataclass, field
from abc import ABC

from object._object_abstract import Object

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
    NONE = 0
    STEEL_ASD_89 = 1
    STEEL_LRFD_89 = 2
    STEEL_PBI_81 = 3
    STEEL_PBI_2002 = 4
    CONCRETE_ACI_89 = 5
    CONCRETE_ACI_95 = 6
    CONCRETE_ACI_91 = 7
    STEEL_AASHTO_98 = 8
    CONCRETE_AASHTO_98 = 9
    CONCRETE_ACI_2002 = 10
    STEEL_LRFD_2002 = 11
    CONCRETE_PBI_2003 = 12
    STEEL_AISI_2002 = 13
    CONCRETE_SNI_2013 = 14
    STEEL_LRFD_2010 = 15
    CONCRETE_ACI_2014 = 16 # SNI_2019
    STEEL_SNI_2019_LRFD = 17 # LRFD_2016
    STEEL_SNI_2019_ASD = 18 # LRFD_2016
    WOOD_SNI_2013 = 18 # SNI_7973

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

@dataclass
class DesignConcreteBase(DesignBase, ABC):
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
class DesignConcreteSlab(DesignConcreteBase):
    tp: float
    
@dataclass
class DesignConcreteWall(DesignConcreteBase):
    tp: float

@dataclass
class DesignConcreteGirder(DesignConcreteBase):
    bw: float
    ht: float
    bf: float
    tf: float

@dataclass
class DesignConcreteBiaxialColumn(DesignConcreteBase):
    b: float
    h: float
    bf: float
    tf: float

@dataclass
class DesignConcreteTeeColumn(DesignConcreteBase):
    b: float
    h: float
    bf: float
    tf: float

@dataclass
class DesignConcreteCircularColumn(DesignConcreteBase):
    d: float

class SectionOption(IntEnum):
    NORMAL = 0
    KING_CORSS = 1
    HONEY_COMB = 2
    MIRROR_BACK = 3

class CompositeOption(IntEnum):
    NONE = 0
    ENCASED = 1
    SLAB = 2
    FILLED = 3

@dataclass
class SteelDesignBase(DesignBase, ABC):
    section_option: SectionOption
    composite_option: CompositeOption
    connection_design: bool

    section: str
    wf2: str
    strong_axis: bool
    h1_ho: int
    space: int

    Es: float
    Fu: float
    Fy: float

    Ag: float
    Rmin: float
    Wx: float
    Wy: float
    An_Ag: float
    material_name: str

    left_haunch_length: float
    left_haunch_height: float

    right_haunch_length: float
    right_haunch_height: float

    Tu: float
    Ty: float

    tension_only: bool

    Ry: float
    Rt: float