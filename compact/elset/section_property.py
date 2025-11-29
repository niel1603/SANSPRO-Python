from dataclasses import dataclass
from abc import ABC, abstractmethod

from object._object_abstract import Object
from SANSPRO.object.material import MaterialIsotropic
from SANSPRO.object.section import SectionThickness, SectionRect, SectionCircle
from SANSPRO.object.design import (
    DesignConcreteBase, 
    ReinforcedConcrete, 
    DesignConcreteSlab, 
    DesignConcreteWall, 
    DesignConcreteGirder, 
    DesignConcreteBiaxialColumn,
    DesignConcreteTeeColumn, 
    DesignConcreteCircularColumn
    )
from SANSPRO.object.design import (
    SteelDesignBase
    )
from SANSPRO.object.elset import Elset

@dataclass
class SectionPropertyReinforcedConcrete:
    bar_dim: float
    tie_dim: float
    cover: float

    @classmethod
    def from_design(cls, design: DesignConcreteBase):
        rc: ReinforcedConcrete = design.reinforced_concrete
        return cls(
            bar_dim=rc.db,
            tie_dim=rc.dbv,
            cover=design.cv,
        )

@dataclass
class SectionPropertyBase(Object, ABC):
    name: str
    material: str

    @classmethod
    @abstractmethod
    def from_section(cls, material, section, design):
        """
        Abstract factory method.
        Must be implemented by subclasses to translate (material, section, design)
        into a concrete SectionProperty instance.
        """
        pass

@dataclass
class SectionPropertyConcrete(SectionPropertyBase):
    rc: SectionPropertyReinforcedConcrete

@dataclass
class SectionPropertySteel(SectionPropertyBase):
    material_design: str

# ==========================================================
# TRANSLATOR
# ==========================================================

# Concrete Slab

@dataclass
class SectionPropertyConcreteSlab(SectionPropertyConcrete):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionThickness,
        design: DesignConcreteSlab,
    ) -> "SectionPropertyConcreteSlab":

        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            rc=SectionPropertyReinforcedConcrete.from_design(design),
        )

# Concrete Wall

@dataclass
class SectionPropertyConcreteWall(SectionPropertyConcrete):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionThickness,
        design: DesignConcreteWall,
    ) -> "SectionPropertyConcreteWall":

        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            rc=SectionPropertyReinforcedConcrete.from_design(design),
        )
    
# Concrete Rectangular Beam

@dataclass
class SectionPropertyConcreteBeam(SectionPropertyConcrete):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionRect,
        design: DesignConcreteGirder,
    ) -> "SectionPropertyConcreteBeam":
        
        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            rc=SectionPropertyReinforcedConcrete.from_design(design),
        )
    
# Concrete Rectangular Biaxial Column

@dataclass
class SectionPropertyConcreteBiaxialColumn(SectionPropertyConcrete):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionRect,
        design: DesignConcreteBiaxialColumn,
    ) -> "SectionPropertyConcreteBiaxialColumn":
        
        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            rc=SectionPropertyReinforcedConcrete.from_design(design),
        )
    
# Concrete Tee or L Column

@dataclass
class SectionPropertyConcreteTeeColumn(SectionPropertyConcrete):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionRect,
        design: DesignConcreteTeeColumn,
    ) -> "SectionPropertyConcreteTeeColumn":
        
        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            rc=SectionPropertyReinforcedConcrete.from_design(design),
        )
    
# Concrete Cicular Column

@dataclass
class SectionPropertyConcreteCircularColumn(SectionPropertyConcrete):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionCircle,
        design: DesignConcreteCircularColumn,
    ) -> "SectionPropertyConcreteCircularColumn":
        
        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            rc=SectionPropertyReinforcedConcrete.from_design(design),
        )
    
# Steel Frame

@dataclass
class SectionPropertySteelFrame(SectionPropertySteel):

    @classmethod
    def from_section(
        cls,
        elset: Elset,
        material: MaterialIsotropic,
        section: SectionCircle,
        design: SteelDesignBase,
    ) -> "SectionPropertySteelFrame":
        
        return cls(
            index=elset.index,
            name=section.name,
            material=material.name,
            material_design=design.material_name,
        )