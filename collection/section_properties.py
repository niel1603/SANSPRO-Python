from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Dict, Type, Tuple

from SANSPRO.object.ObjectAbstract import Object
from SANSPRO.object.material import MaterialIsotropic
from SANSPRO.object.Section import SectionThickness, SectionRect, SectionCircle
from SANSPRO.object.design import DesignBase, ReinforcedConcrete, DesignConcreteSlab, DesignConcreteWall, DesignConcreteGirder, DesignConcreteBiaxialColumn, DesignConcreteCircularColumn
from SANSPRO.object.elset import Elset

from SANSPRO.collection.CollectionAbstract import Collection, CollectionParser
# from SANSPRO.collection.materials import Materials
# from SANSPRO.collection.Sections import Sections
# from SANSPRO.collection.designs import Designs


from collections import defaultdict
from dataclasses import dataclass

class SectionProperties(Collection["SectionPropertyBase"]):
    pass

    def split_by_class(self) -> Dict[str, "SectionProperties"]:
        """
        Split collection into sub-collections grouped by class name.
        Example:
            {
                "SectionPropertyConcreteSlab": SectionProperties([...]),
                "SectionPropertyConcreteBeam": SectionProperties([...]),
            }
        """
        groups = defaultdict(list)
        for obj in self.objects:
            class_name = obj.__class__.__name__
            groups[class_name].append(obj)
        return {name: SectionProperties(objs) for name, objs in groups.items()}

@dataclass
class SectionPropertyReinforcedConcrete:
    bar_dim: float
    tie_dim: float
    cover: float

    @classmethod
    def from_design(cls, design: DesignBase):
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
    rc: SectionPropertyReinforcedConcrete

    @classmethod
    @abstractmethod
    def from_section(cls, material, section, design):
        """
        Abstract factory method.
        Must be implemented by subclasses to translate (material, section, design)
        into a concrete SectionProperty instance.
        """
        pass


# ==========================================================
# TRANSLATOR
# ==========================================================

# Concrete Slab

@dataclass
class SectionPropertyConcreteSlab(SectionPropertyBase):

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
class SectionPropertyConcreteWall(SectionPropertyBase):

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
class SectionPropertyConcreteBeam(SectionPropertyBase):

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
class SectionPropertyConcreteBiaxialColumn(SectionPropertyBase):

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
    
# Concrete Cicular Column

@dataclass
class SectionPropertyConcreteCircularColumn(SectionPropertyBase):

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
    
# ==========================================================
# ADAPTER 
# ==========================================================

class SectionPropertyAdapter:
    """
    Adapter to translate between Elset definitions and SectionProperty objects,
    or load them directly from Excel.
    """

    _MAP: Dict[Tuple[str, str, str], Type["SectionPropertyBase"]] = {
        ("ISOTROPIC", "THICKNESS", "CONCRETE_SLAB"): SectionPropertyConcreteSlab,
        ("ISOTROPIC", "RECT", "CONCRETE_GIRDER"): SectionPropertyConcreteBeam,
        ("ISOTROPIC", "RECT", "CONCRETE_BCOL"): SectionPropertyConcreteBiaxialColumn,
        ("ISOTROPIC", "CIRCLE", "CONCRETE_CCOL"): SectionPropertyConcreteCircularColumn,
        ("ISOTROPIC", "THICKNESS", "CONCRETE_WALL"): SectionPropertyConcreteWall,
    }

    # ------------------------------------------------------
    # INIT — optional dependencies
    # ------------------------------------------------------
    def __init__(self, materials=None, sections=None, designs=None):
        """
        Initialize adapter.
        You can omit materials/sections/designs when using from_excel().
        """
        self.materials = materials
        self.sections = sections
        self.designs = designs

    # ------------------------------------------------------
    # 1. Elset-based methods (use full context)
    # ------------------------------------------------------
    def from_elset(self, elset: Elset):
        if not (self.materials and self.sections and self.designs):
            raise RuntimeError("materials, sections, and designs are required for from_elset()")

        mat = self.materials.get(elset.material.index)
        sec = self.sections.get(elset.section.index)
        des = self.designs.get(elset.design.index)

        key = (
            mat.type_name.upper(),
            sec.type_name.upper(),
            des.type_name.upper(),
        )

        if key not in self._MAP:
            raise ValueError(f"No SectionProperty mapping for combination {key}")

        cls = self._MAP[key]
        return cls.from_section(elset, mat, sec, des)

    def from_elsets(self, elsets):
        if not (self.materials and self.sections and self.designs):
            raise RuntimeError("materials, sections, and designs are required for from_elsets()")

        section_properties = []
        for idx in elsets.index_list():
            elset = elsets.get(idx)
            try:
                sp = self.from_elset(elset)
                section_properties.append(sp)
            except Exception as ex:
                print(f"[WARN] Elset {idx} skipped: {ex}")

        return SectionProperties(section_properties)

    # ------------------------------------------------------
    # 2. Excel-based loader (no dependencies)
    # ------------------------------------------------------
    @classmethod
    def from_excel(cls, import_path: str) -> "SectionProperties":
        """
        Load section property data directly from Excel into SectionProperties.
        """

        from util.excel_import import import_multiple_collections_from_excel, add_prefix_dict_keys

        # Read Excel
        data = import_multiple_collections_from_excel(
            import_path,
            {
                "ConcreteSlab": SectionPropertyConcreteSlab,
                "ConcreteWall": SectionPropertyConcreteWall,
                "ConcreteBeam": SectionPropertyConcreteBeam,
                "ConcreteBiaxialColumn": SectionPropertyConcreteBiaxialColumn,
                "ConcreteCircularColumn": SectionPropertyConcreteCircularColumn,
            },
        )

        # Prefix for consistent naming
        section_dict = add_prefix_dict_keys(data, "SectionProperty")

        # Merge into one SectionProperties collection
        all_props = []
        for subset in section_dict.values():
            if isinstance(subset, list):
                all_props.extend(subset)

        return SectionProperties(all_props)