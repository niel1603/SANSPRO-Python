import re
import copy
from typing import Type, Optional, List, Dict, Tuple, Union, Set
from types import SimpleNamespace
from collections import OrderedDict
from dataclasses import asdict, is_dataclass, replace

from SANSPRO.model.Model import Model
from SANSPRO.object.elset import Elset
from SANSPRO.collection.CollectionAbstract import Collection, CollectionParser, ObjectCollectionQuery, ObjectCollectionEngine, ObjectCollectionAdapter

from SANSPRO.object.material import MaterialBase
from SANSPRO.object.Section import SectionBase
from SANSPRO.object.design import DesignBase

from SANSPRO.collection.materials import Materials
from SANSPRO.collection.Sections import Sections
from SANSPRO.collection.designs import Designs

from SANSPRO.collection.materials import MaterialsFactory
from SANSPRO.collection.Sections import SectionsFactory
from SANSPRO.collection.designs import DesignFactory

from SANSPRO.collection.materials import MaterialsComparer
from SANSPRO.collection.Sections import SectionsComparer
from SANSPRO.collection.designs import DesignsComparer

from SANSPRO.variable.Parameter import ParameterParse, ParameterAdapter

class Elsets(Collection[Elset]):
    header = 'ELSET'

    # ------------------------------------------------------------
    # Lookup by Design
    # ------------------------------------------------------------

    def get_by_design(self, design: Union[DesignBase, int, str]) -> Optional[Elset]:
        # Case 1 — direct design instance
        if isinstance(design, DesignBase):
            target_name = design.name

        # Case 2 — design index
        elif isinstance(design, int):
            # convert index → name
            for e in self.objects:
                if e.design.index == design:
                    target_name = e.design.name
                    break
            else:
                return None

        # Case 3 — name directly
        elif isinstance(design, str):
            target_name = design

        else:
            raise TypeError("design must be DesignBase, int, or str")

        # Resolve via name
        for e in self.objects:
            if e.design.name == target_name:
                return e

        return None

    def get_summary(self) -> List[dict]:
        """
        Produce a summary list for all Elsets.
        Each entry contains:
            index, material_name, section_name, design_name, texture
        """
        summary = []
        for e in self.objects:
            summary.append({
                "index": e.index,
                "material": e.material.name,
                "section": e.section.name,
                "design": e.design.name,
                "texture": e.texture,
            })
        return summary
    
    def print_summary(self):
        for e in self.objects:
            print(
                f"{e.index:3d}  "
                f"MAT={e.material.name:<20}  "
                f"SEC={e.section.name:<20}  "
                f"DES={e.design.name:<20}  "
                f"TX={e.texture}"
            )
    
class ElsetsParse(CollectionParser[Model, Elset, Elsets]):
    LINES_PER_ITEM = 1

    @classmethod
    def get_collection(cls) -> Type[Elsets]:
        return Elsets

    @classmethod
    def parse_line(cls, lines: List[str], *, materials, sections, designs) -> Elset:
        tokens = [line.split() for line in lines]
        return cls._parse_elset(tokens, materials, sections, designs)

    @staticmethod
    def _parse_elset(tokens: List[List[str]],
                      materials: "Materials",
                      sections: "Sections",
                      designs: "Designs") -> Elset:

        l0 = tokens[0]
        idx = int(l0[0])
        mat_i = int(l0[1])
        sec_i = int(l0[2])
        des_i = int(l0[3])
        tex_i = int(l0[4])

        mat = materials.get(mat_i)
        sec = sections.get(sec_i)
        des = designs.get(des_i)

        if mat is None:
            raise ValueError(f"Elset {idx}: material index {mat_i} not found")
        if sec is None:
            raise ValueError(f"Elset {idx}: section index {sec_i} not found")
        if des is None:
            raise ValueError(f"Elset {idx}: design index {des_i} not found")

        return Elset(
            index=idx,
            material=mat,
            section=sec,
            design=des,
            texture=tex_i,
        )

    
from SANSPRO.collection.section_properties import (
    SectionPropertyConcreteSlab, 
    SectionPropertyConcreteBeam, 
    SectionPropertyConcreteBiaxialColumn, 
    SectionPropertyConcreteCircularColumn,
    SectionPropertyConcreteWall, 
    )
from SANSPRO.object.material import (
    MaterialIsotropic,
    MaterialSpring
    )
from SANSPRO.collection.elsets import Elsets
from SANSPRO.collection.section_properties import SectionProperties

class ElsetsAdapter(ObjectCollectionAdapter[Model, Elset, Elsets]):

    @classmethod
    def update_var(cls, elsets: Elsets, model: Model) -> Model:

        parameter = ParameterParse.from_mdl(model)
        parameter.elset = len(elsets.objects)
        model = ParameterAdapter.to_model(parameter, model)

        return model

    @classmethod
    def format_line(cls, elset: Elset) -> str:
        index = int(elset.index)

        # NEW typed Elset (material/section/design are objects)
        if hasattr(elset.material, "index"):
            material = elset.material.index
            section  = elset.section.index
            design   = elset.design.index

        # OLD parsed Elset (material/section/design are ints)
        else:
            material = elset.material
            section  = elset.section
            design   = elset.design

        texture = int(elset.texture)

        return f"  {index:>2}  {material:>2}  {section:>2} {design:>2}  {texture}"

    # ======================================================
    # PUBLIC API
    # ======================================================
    @classmethod
    def from_section_properties(cls, section_props: SectionProperties):
        """
        Full pipeline:
        1. Build index maps
        2. Normalize section properties (reindex)
        3. Build material/section/design objects
        4. Build Elset objects referencing these objects
        5. Return everything as strongly typed collections
        """

        # --------------------------------------------------
        # 1) Build maps (material→id, section→id, design→id)
        # --------------------------------------------------
        type_order, material_map, section_prop_map, design_map = cls._build_index_maps(section_props)

        # --------------------------------------------------
        # 2) Normalize SectionProperty objects (reindexed)
        # --------------------------------------------------
        normalized_sp = cls._normalize_section_properties(section_props, type_order)

        # --------------------------------------------------
        # 3) Build typed Material/Section/Design collections
        # --------------------------------------------------
        materials = cls._build_materials(material_map)
        material_map, materials = cls._reorder_material_map(material_map, materials)
        sections  = cls._build_sections(section_prop_map, normalized_sp)
        designs   = cls._build_designs(design_map, 
                                       normalized_sp, 
                                       material_map, 
                                       materials, 
                                       sections)

        # --------------------------------------------------
        # 4) Build Elsets that reference typed objects
        # --------------------------------------------------
        elsets = cls._build_elsets(
            normalized_sp,
            material_map, section_prop_map, design_map,
            materials, sections, designs
        )

        return (elsets, materials, sections, designs)

    # ======================================================
    # STAGE 1 — MAP BUILDING
    # ======================================================
    @classmethod
    def _build_index_maps(cls, section_props):
        type_order = [
            SectionPropertyConcreteSlab,
            SectionPropertyConcreteBeam,
            SectionPropertyConcreteBiaxialColumn,
            SectionPropertyConcreteCircularColumn,
            SectionPropertyConcreteWall,
        ]

        ordered = sorted(section_props.objects, key=lambda sp: type_order.index(type(sp)))

        material_map = OrderedDict()
        section_map  = OrderedDict()
        design_map   = OrderedDict()

        for sp in ordered:
            mkey = sp.material
            skey = (sp.section_property_type, sp.name)

            if hasattr(sp, "rc") and sp.rc:
                dkey = (sp.section_property_type, sp.name, cls._key(sp.rc))
            else:
                dkey = (sp.section_property_type, sp.name)

            cls._next_id(material_map, mkey)
            cls._next_id(section_map, skey)
            cls._next_id(design_map, dkey)

        return type_order, material_map, section_map, design_map

    # ======================================================
    # STAGE 2 — NORMALIZATION
    # ======================================================
    @staticmethod
    def _normalize_section_properties(section_props, type_order):
        ordered = sorted(section_props.objects, key=lambda sp: type_order.index(type(sp)))

        normalized = []
        for new_index, sp in enumerate(ordered, start=1):
            sp.index = new_index
            normalized.append(sp)

        return type(section_props)(normalized)

    # ======================================================
    # STAGE 3 — BUILD MATERIALS
    # ======================================================
    @staticmethod
    def _build_materials(material_map):
        factory = MaterialsFactory(material_map)
        return factory.create_all()

    # ======================================================
    # STAGE 4 — BUILD SECTIONS
    # ======================================================
    @staticmethod
    def _build_sections(section_prop_map, normalized_sp):
        sp_by_index = {sp.index: sp for sp in normalized_sp.objects}
        factory = SectionsFactory(section_prop_map, sp_by_index)
        return factory.create_all()

    # ======================================================
    # STAGE 5 — BUILD DESIGNS
    # ======================================================
    @staticmethod
    def _build_designs(design_map, normalized_sp, material_map, materials, sections):
        sp_by_index = {sp.index: sp for sp in normalized_sp.objects}

        factory = DesignFactory(
            design_map=design_map,
            design_props=sp_by_index,
            material_map=material_map,   # dict[str → int]
            materials=materials,           # <- MUST pass Materials
            sections=sections,
        )
        return factory.create_all()
    # ======================================================
    # STAGE 6 — BUILD FINAL ELSETS (typed)
    # ======================================================

    @staticmethod
    def _build_elsets(
        normalized_sp,
        material_map, section_map, design_map,
        materials, sections, designs
    ):
        elset_objs = []

        for sp in normalized_sp.objects:
            mid = material_map[sp.material]

            # SECTION KEY
            skey = (type(sp), sp.name)

            # DESIGN KEY (class + name [+ rc signature])
            if hasattr(sp, "rc") and sp.rc:
                dkey = (type(sp), sp.name, ElsetsAdapter._key(sp.rc))
            else:
                dkey = (type(sp), sp.name)

            sect_id = section_map[skey]
            des_id  = design_map[dkey]

            elset_objs.append(
                Elset(
                    index=sp.index,
                    material=materials.get(mid),
                    section=sections.get(sect_id),
                    design=designs.get(des_id),
                    texture=0,
                )
            )

        return Elsets(elset_objs)
    
    # ==========================================================
    # Internal helpers
    # ==========================================================
    @staticmethod
    def _next_id(mapping, key):
        if key not in mapping:
            mapping[key] = len(mapping) + 1
        return mapping[key]

    @staticmethod
    def _key(obj):
        """
        Convert RC objects (or other dataclasses) into hashable, comparable tuples.
        Used for building design_map keys.
        """
        if obj is None or isinstance(obj, (int, float, str, bool)):
            return obj

        # dataclass → dict
        if is_dataclass(obj):
            obj = asdict(obj)

        # dict → sorted tuple of (key, normalized_value)
        if isinstance(obj, dict):
            return tuple(
                (k, ElsetsAdapter._key(v))
                for k, v in sorted(obj.items())
            )

        # fallback
        return repr(obj)

    @classmethod
    def _build_index_maps(cls, section_props):

        type_order = [
            SectionPropertyConcreteSlab,
            SectionPropertyConcreteBeam,
            SectionPropertyConcreteBiaxialColumn,
            SectionPropertyConcreteCircularColumn,
            SectionPropertyConcreteWall,
        ]

        # sort by class order
        ordered = sorted(
            section_props.objects,
            key=lambda sp: type_order.index(type(sp)),
        )

        material_map = OrderedDict()
        section_map  = OrderedDict()
        design_map   = OrderedDict()

        for sp in ordered:
            # MATERIAL KEY
            mkey = sp.material

            # SECTION KEY (class + name)
            skey = (type(sp), sp.name)

            # DESIGN KEY (class + name [+ rc signature])
            if hasattr(sp, "rc") and sp.rc is not None:
                dkey = (type(sp), sp.name, cls._key(sp.rc))
            else:
                dkey = (type(sp), sp.name)

            cls._next_id(material_map, mkey)
            cls._next_id(section_map,  skey)
            cls._next_id(design_map,   dkey)

        return type_order, material_map, section_map, design_map

    
    @staticmethod
    def _reorder_material_map(material_map, materials=None):
        """
        Reorder materials so that indices follow:
            1) material type (ISOTROPIC → SPRING → others)
            2) within the same type: numeric suffix (e.g. fc-20 < fc-25 < fc-30)

        This function:
            - rebuilds the OrderedDict material_map
            - reassigns Material.index to match the new order
            - rebuilds the internal materials._index table
            - returns (new_material_map, new_materials)
        """

        MATERIAL_TYPE_ORDER = [
            MaterialIsotropic,
            MaterialSpring,
        ]

        # Build type lookup if materials collection is provided
        type_lookup = {}
        if materials is not None:
            for mat in materials.objects:
                type_lookup[mat.index] = type(mat)  # old index → class

        def _split_mkey(mkey: str):
            m = re.match(r"^([A-Za-z]+)(\d+\.?\d*)$", mkey)
            if not m:
                raise ValueError(f"Invalid format for prefix+value: '{mkey}'")
            prefix, num = m.groups()
            return prefix, float(num)

        def _sort_key(mkey):
            old_idx = material_map[mkey]

            # sort by type
            if materials is not None:
                cls = type_lookup.get(old_idx)
                if cls in MATERIAL_TYPE_ORDER:
                    type_rank = MATERIAL_TYPE_ORDER.index(cls)
                else:
                    type_rank = len(MATERIAL_TYPE_ORDER) + 1
            else:
                type_rank = 0

            # numeric sort inside same type
            strength = _split_mkey(mkey)

            return (type_rank, strength)

        # ======================================================
        # 1) Sort keys by (type_rank, numeric_strength)
        # ======================================================
        sorted_keys = sorted(material_map.keys(), key=_sort_key)

        # ======================================================
        # 2) Build new material_map with new indices
        # ======================================================
        new_map = OrderedDict()
        for new_idx, key in enumerate(sorted_keys, start=1):
            new_map[key] = new_idx

        # ======================================================
        # 3) Rewrite Material.index to match the new order
        # ======================================================
        if materials is not None:
            # reverse lookup: old_index → key
            reverse = {old_idx: key for key, old_idx in material_map.items()}

            for mat in materials.objects:
                old_key = reverse[mat.index]
                new_index = new_map[old_key]
                mat.index = new_index                     # update index

            # rebuild internal index dictionary
            materials._index = {mat.index: mat for mat in materials.objects}

            # also rebuild reverse_index
            materials._reverse_index = {id(mat): mat.index for mat in materials.objects}

        # ======================================================
        # 4) Return (new_map, materials)
        # ======================================================
        return new_map, materials


class ElsetMerger:
    """
    Central merger. Design ordering dictates Section ordering,
    which dictates Material ordering. Elsets are rebuilt in the
    same sequence as merged Designs.

    Output:
        merged_elsets,
        merged_materials,
        merged_sections,
        merged_designs,
        reorder_design_map
    """

    def __init__(
        self,
        existing_elsets: Elsets,
        imported_elsets: Elsets,
        used_elsets: Optional[Set[int]] = None,
        existing_materials: Optional[Materials] = None,
        imported_materials: Optional[Materials] = None,
    ) -> None:

        self.existing = existing_elsets
        self.imported = imported_elsets
        self.used_elsets = used_elsets or set()

        # protect originals
        self.existing_materials = copy.deepcopy(existing_materials)
        self.imported_materials = copy.deepcopy(imported_materials)

    # ----------------------------------------------------------
    def merge(self):
        """
        Main merge routine:
         1. merge materials
         2. merge designs → become the master ordering
         3. derive sections order directly from merged designs
         4. rebuild elsets
        """

        # ------------------------------------------------------
        # Extract underlying typed objects
        # ------------------------------------------------------
        existing_designs  = Designs([e.design  for e in self.existing])
        imported_designs  = Designs([e.design  for e in self.imported])

        existing_sections = Sections([e.section for e in self.existing])
        imported_sections = Sections([e.section for e in self.imported])

        # ------------------------------------------------------
        # 1) Merge Materials
        # ------------------------------------------------------
        materials_cmp = MaterialsComparer(self.existing_materials, self.imported_materials)
        merged_materials, _, _ = materials_cmp.merge_and_reorder(unique_attr="name")

        for m_m in merged_materials:
            print(m_m.name)

        # ------------------------------------------------------
        # 2) Merge Designs (master ordering)
        # ------------------------------------------------------
        designs_cmp = DesignsComparer(existing_designs, imported_designs)
        merged_designs, reorder_design_map, _ = designs_cmp.merge_and_reorder(
            unique_attr="name",
            remove_missing=False,
            used_elsets=self.used_elsets,
        )

        # ------------------------------------------------------
        # 3) Sections follow the merged design order
        # ------------------------------------------------------
        merged_sections = self._sections_by_design_order(
            merged_designs,
            existing_sections,
            imported_sections
        )

        # ------------------------------------------------------
        # 4) Rebuild Elsets in merged order
        # ------------------------------------------------------
        merged_elsets, merged_sections = self._rebuild_elsets(
            merged_designs,
            merged_sections,
            merged_materials,
        )

        return (
            merged_elsets,
            merged_materials,
            merged_sections,
            merged_designs,
            reorder_design_map,
        )

    # ----------------------------------------------------------
    # Build sections strictly following design order (Option A)
    # ----------------------------------------------------------
    def _sections_by_design_order(
        self,
        merged_designs: Designs,
        existing_sections: Sections,
        imported_sections: Sections,
    ) -> Sections:

        ordered = []

        for des in merged_designs:
            name = des.name

            sec = (
                imported_sections.get_by_name(name)
                or existing_sections.get_by_name(name)
            )

            if sec is None:
                raise KeyError(f"Section not found for design '{name}'")

            ordered.append(sec)

        return Sections(ordered)

    # ----------------------------------------------------------
    # REBUILD ELSETS
    # ----------------------------------------------------------
    def _rebuild_elsets(
        self,
        merged_designs: Designs,
        merged_sections: Sections,
        merged_materials: Materials,
    ) -> Tuple[Elsets, Sections]:

        new_elsets = []
        new_sections = []

        for new_idx, des in enumerate(merged_designs, start=1):

            # SECTION (clone with correct index)
            sec_old = merged_sections.get_by_name(des.name)
            if sec_old is None:
                raise KeyError(f"Section not found for design '{des.name}'")

            sec_new = replace(sec_old, index=new_idx)
            new_sections.append(sec_new)

            # SELECT elset source: prefer imported
            imp = self.imported.get_by_design(des)
            exs = self.existing.get_by_design(des)
            chosen = imp or exs
            if chosen is None:
                raise KeyError(f"No elset found for design '{des.name}'")

            # MATERIAL
            mat_old = chosen.material
            mat_new = merged_materials.get_by_name(mat_old.name)
            if mat_new is None:
                raise KeyError(f"Material '{mat_old.name}' not found in merged_materials")

            # BUILD NEW ELSET
            new_elset = Elset(
                index=new_idx,
                material=mat_new,
                section=sec_new,
                design=des,
                texture=chosen.texture,
            )
            new_elsets.append(new_elset)

        return Elsets(new_elsets), Sections(new_sections)
