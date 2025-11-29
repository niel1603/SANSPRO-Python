from typing import Dict, Type, Tuple
from collections import defaultdict

from SANSPRO.object.elset import Elset
from SANSPRO.collection._collection_abstract import Collection

from compact.elset.section_property import (
    SectionPropertyBase,
    SectionPropertyConcreteSlab,
    SectionPropertyConcreteWall,
    SectionPropertyConcreteBeam,
    SectionPropertyConcreteBiaxialColumn,
    SectionPropertyConcreteTeeColumn,
    SectionPropertyConcreteCircularColumn,
    SectionPropertySteelFrame
)

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
        ("ISOTROPIC", "TEE", "CONCRETE_TCOL"): SectionPropertyConcreteTeeColumn,
        ("ISOTROPIC", "CIRCLE", "CONCRETE_CCOL"): SectionPropertyConcreteCircularColumn,
        ("ISOTROPIC", "THICKNESS", "CONCRETE_WALL"): SectionPropertyConcreteWall,
        ("ISOTROPIC", "USER", "STEEL_FRAME"): SectionPropertySteelFrame,
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
                "ConcreteTeeColumn": SectionPropertyConcreteTeeColumn,
                "ConcreteCircularColumn": SectionPropertyConcreteCircularColumn,
                "SteelFrame": SectionPropertySteelFrame,
            },
        )

        # Prefix keys
        section_dict = add_prefix_dict_keys(data, "SectionProperty")

        # Merge into one flat list
        all_props = []
        for subset in section_dict.values():
            if isinstance(subset, list):
                all_props.extend(subset)

        # ----------------------------------------------------------------------
        # Detect and warn about duplicated section names
        # ----------------------------------------------------------------------
        seen = set()
        unique_props = []
        duplicates = []

        for sp in all_props:
            if sp.name in seen:
                duplicates.append(sp.name)
            else:
                seen.add(sp.name)
                unique_props.append(sp)

        if duplicates:
            print(f"[WARNING] Duplicated section properties detected (kept first occurrence):")
            for name in duplicates:
                print(f"  - {name}")

        # Return filtered SectionProperties
        return SectionProperties(unique_props)
