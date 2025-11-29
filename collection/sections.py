import re
from typing import Type, List, Dict, Tuple

from SANSPRO.model.model import Model
from SANSPRO.object.section import (
    SectionBase, 
    SectionThickness, 
    SectionRect,
    SectionTee, 
    SectionCircle, 
    SectionUser
    )

from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

from SANSPRO.variable.parameter import ParameterParse, ParameterAdapter

class Sections(Collection[SectionBase]):
    header = 'SECTION'

class SectionsParse(CollectionParser[Model, SectionBase, Sections]):
    LINES_PER_ITEM = 2

    @classmethod
    def get_collection(cls) -> Type[Sections]:
        return Sections

    @classmethod
    def parse_line(cls, lines: List[str]) -> SectionBase:
        main, sub = lines
        parts = main.split()
        section_type = parts[2].upper()

        if section_type == "THICKNESS":
            return cls._parse_thickness(parts, sub)
        elif section_type == "RECT":
            return cls._parse_rect(parts, sub)
        elif section_type == "TEE":
            return cls._parse_tee(parts, sub)
        elif section_type == "CIRCLE":
            return cls._parse_circle(parts, sub)
        elif section_type == "USER":
            return cls._parse_user(parts, sub)
        else:
            raise ValueError(f"Unsupported SECTION type: {section_type}")

    # --------------------------------------------------
    # Sub-parsers for specific section types
    # --------------------------------------------------
    @staticmethod
    def _parse_thickness(parts: List[str], sub: str) -> SectionThickness:

        # store unknown variable
        misc = (
            int(parts[3]),
            int(parts[4]),
            int(parts[5]),
            int(parts[6]),
            float(parts[7]),
            float(parts[8]),
        )

        return SectionThickness(
            index=int(parts[0]),
            type_index=int(parts[1]),
            type_name=parts[2],
            misc=misc,
            name=parts[9],
            thickness=float(sub.strip())
        )


    @staticmethod
    def _parse_rect(parts: List[str], sub: str) -> "SectionRect":
        # split sub line into numeric parts
        nums = [float(x) for x in sub.split()]  # [b, ht, bf, tf]
        b, ht, bf, tf = nums

        # warn if b != bf
        if abs(b - bf) > 1e-6:  # tolerance for floating point
            print(f"[WARN] RECT section at index {parts[0]}: width mismatch (b={b}, bf={bf})")

        misc = (
            int(parts[3]),
            int(parts[4]),
            int(parts[5]),
            int(parts[6]),
            float(parts[7]),
            float(parts[8]),
        )

        return SectionRect(
            index=int(parts[0]),
            type_index=int(parts[1]),
            type_name=parts[2],
            misc=misc,
            name=parts[9],
            width=b,          # single width field
            height=ht,
            slab_thick=tf
        )
    
    @staticmethod
    def _parse_tee(parts: List[str], sub: str) -> "SectionTee":
        nums = [float(x) for x in sub.split()]
        b, ht, tw, tf = nums

        misc = (
            int(parts[3]),
            int(parts[4]),
            int(parts[5]),
            int(parts[6]),
            float(parts[7]),
            float(parts[8]),
        )

        return SectionTee(
            index=int(parts[0]),
            type_index=int(parts[1]),
            type_name=parts[2],
            misc=misc,
            name=parts[9],
            width=b,
            height=ht,
            thick_web=tw,
            thick_flange=tf
        )
    
    @staticmethod
    def _parse_circle(parts: List[str], sub: str) -> "SectionCircle":
        # store unknown variable
        misc = (
            int(parts[3]),
            int(parts[4]),
            int(parts[5]),
            int(parts[6]),
            float(parts[7]),
            float(parts[8]),
        )

        return SectionCircle(
            index=int(parts[0]),
            type_index=int(parts[1]),
            type_name=parts[2],
            misc=misc,
            name=parts[9],
            diameter=float(sub.strip())
        )
    
    @staticmethod
    def _parse_user(parts: List[str], sub: str) -> SectionUser:
        nums = [x for x in sub.split()]  # [b, ht, bf, tf]
        ss, sa = nums
        # store unknown variable
        misc = (
            int(parts[3]),
            int(parts[4]),
            int(parts[5]),
            int(parts[6]),
            float(parts[7]),
            float(parts[8]),
        )

        return SectionUser(
            index=int(parts[0]),
            type_index=int(parts[1]),
            type_name=parts[2],
            misc=misc,
            name=parts[9],
            steel_sect=str(ss),
            strong_axis=bool(int(sa))
        )

class SectionsAdapter(ObjectCollectionAdapter[Model, SectionBase, Sections]):

    @classmethod
    def update_var(cls, sections: Sections, model: Model) -> Model:

        parameter = ParameterParse.from_mdl(model)
        parameter.section_properties = len(sections.objects)
        model = ParameterAdapter.to_model(parameter, model)

        return model

    @classmethod
    def format_line(cls, sections: SectionBase) -> str:

        if sections.type_name == "THICKNESS":
            return cls._format_line_thickness(sections)
        elif sections.type_name == "RECT":
            return cls._format_line_rect(sections)
        elif sections.type_name == "TEE":
            return cls._format_line_tee(sections)
        elif sections.type_name == "CIRCLE":
            return cls._format_line_circle(sections)
        elif sections.type_name == "USER":
            return cls._format_line_user(sections)
        else:
            print(f"[WARN] Skipping unsupported SECTION type: {sections.type_name}")
            return None
    
    @classmethod
    def _format_line_thickness(cls, s: SectionThickness) -> str:

        i = int(s.index)
        t_i = int(s.type_index)
        t_n = str(s.type_name)

        m_0, m_1, m_2, m_3, m_4, m_5 = s.misc
        m_0 = int(m_0)
        m_1 = int(m_1)
        m_2 = int(m_2)
        m_3 = int(m_3)
        m_4 = float(m_4)
        m_4 = float(m_5)

        n = str(s.name)

        t = cls._norm_float(s.thickness)

        line1 = f'{i:>4}{t_i:>4} {t_n:<12} {m_0} {m_1} {m_2} {m_3}{m_4:>8.2f}{m_5:>8.2f} {n}'
        line2 = f'      {t}'

        line = f'{line1}\n{line2}'
        return line
    
    @classmethod
    def _format_line_rect(cls, s: SectionRect) -> str:

        i = int(s.index)
        t_i = int(s.type_index)
        t_n = str(s.type_name)

        m_0, m_1, m_2, m_3, m_4, m_5 = s.misc
        m_0 = int(m_0)
        m_1 = int(m_1)
        m_2 = int(m_2)
        m_3 = int(m_3)
        m_4 = float(m_4)
        m_4 = float(m_5)

        n = str(s.name)

        w = cls._norm_float(s.width)
        h = cls._norm_float(s.height)
        s_t = cls._norm_float(s.slab_thick)

        line1 = f'{i:>4}{t_i:>4} {t_n:<12} {m_0} {m_1} {m_2} {m_3}{m_4:>8.2f}{m_5:>8.2f} {n}'
        line2 = f'      {w} {h} {w} {s_t}'

        line = f'{line1}\n{line2}'
        return line
    
    @classmethod
    def _format_line_tee(cls, s: SectionTee) -> str:

        i = int(s.index)
        t_i = int(s.type_index)
        t_n = str(s.type_name)

        m_0, m_1, m_2, m_3, m_4, m_5 = s.misc
        m_0 = int(m_0)
        m_1 = int(m_1)
        m_2 = int(m_2)
        m_3 = int(m_3)
        m_4 = float(m_4)
        m_4 = float(m_5)

        n = str(s.name)

        w = cls._norm_float(s.width)
        h = cls._norm_float(s.height)
        t_w = cls._norm_float(s.thick_web)
        t_f = cls._norm_float(s.thick_flange)

        line1 = f'{i:>4}{t_i:>4} {t_n:<12} {m_0} {m_1} {m_2} {m_3}{m_4:>8.2f}{m_5:>8.2f} {n}'
        line2 = f'      {w} {h} {t_w} {t_f}'

        line = f'{line1}\n{line2}'
        return line
    
    @classmethod
    def _format_line_circle(cls, s: SectionCircle) -> str:

        i = int(s.index)
        t_i = int(s.type_index)
        t_n = str(s.type_name)

        m_0, m_1, m_2, m_3, m_4, m_5 = s.misc
        m_0 = int(m_0)
        m_1 = int(m_1)
        m_2 = int(m_2)
        m_3 = int(m_3)
        m_4 = float(m_4)
        m_4 = float(m_5)

        n = str(s.name)

        d = cls._norm_float(s.diameter)

        line1 = f'{i:>4}{t_i:>4} {t_n:<12} {m_0} {m_1} {m_2} {m_3}{m_4:>8.2f}{m_5:>8.2f} {n}'
        line2 = f'      {d}'

        line = f'{line1}\n{line2}'
        return line
    
    @classmethod
    def _format_line_user(cls, s: SectionUser) -> str:

        i = int(s.index)
        t_i = int(s.type_index)
        t_n = str(s.type_name)

        m_0, m_1, m_2, m_3, m_4, m_5 = s.misc
        m_0 = int(m_0)
        m_1 = int(m_1)
        m_2 = int(m_2)
        m_3 = int(m_3)
        m_4 = float(m_4)
        m_4 = float(m_5)

        n = str(s.name)

        sa = int(s.strong_axis)

        line1 = f'{i:>4}{t_i:>4} {t_n:<12} {m_0} {m_1} {m_2} {m_3}{m_4:>8.2f}{m_5:>8.2f} {n}'
        line2 = f'     {n} {sa}'

        line = f'{line1}\n{line2}'
        return line

from collections import OrderedDict
from compact.elset.section_properties import (
    SectionPropertyConcreteSlab, 
    SectionPropertyConcreteBeam, 
    SectionPropertyConcreteBiaxialColumn, 
    SectionPropertyConcreteTeeColumn, 
    SectionPropertyConcreteCircularColumn,
    SectionPropertyConcreteWall, 
    SectionPropertySteelFrame,
    )

class SectionsFactory:
    """
    Factory that builds Section objects from a section_map and section property instances,
    using an explicit type mapping instead of section_property_type strings.
    """

    # -----------------------------------------------------------
    # TYPE MAPPING — determines which SectionBase subclass to build
    # -----------------------------------------------------------
    TYPE_MAP: Dict[type, str] = {
        SectionPropertyConcreteSlab: "THICKNESS",
        SectionPropertyConcreteWall: "THICKNESS",
        SectionPropertyConcreteBeam: "RECT",
        SectionPropertyConcreteBiaxialColumn: "RECT",
        SectionPropertyConcreteTeeColumn: "TEE",
        SectionPropertyConcreteCircularColumn: "CIRCLE",
        SectionPropertySteelFrame: "USER",
    }

    def __init__(self, section_map: "OrderedDict[tuple[str, str], int]", section_props: Dict[int, object]):
        """
        section_map: OrderedDict[((section_type, name), index)]
        section_props: dict[index -> SectionPropertyConcrete*]
        """
        self.section_map = section_map
        self.section_props = section_props

    # ============================================================
    # MAIN ENTRY
    # ============================================================
    def create_section(self, section_key: Tuple[str, str]) -> SectionBase:
        if section_key not in self.section_map:
            raise KeyError(f"Section key {section_key} not found in section_map")

        index = self.section_map[section_key]
        section_prop = self.section_props.get(index)
        if not section_prop:
            raise KeyError(f"Section index {index} not found in section_props")

        section_cls_name = type(section_prop)
        if section_cls_name not in self.TYPE_MAP:
            raise ValueError(f"No mapping found for {section_cls_name.__name__}")

        type_name = self.TYPE_MAP[section_cls_name]
        name = section_prop.name

        if type_name == "THICKNESS":
            return self._create_thickness(section_prop, index, name)
        elif type_name == "RECT":
            return self._create_rect(section_prop, index, name)
        elif type_name == "TEE":
            return self._create_tee(section_prop, index, name)
        elif type_name == "CIRCLE":
            return self._create_circle(section_prop, index, name)
        elif type_name == "USER":
            return self._create_user(section_prop, index, name)
        else:
            raise ValueError(f"Unsupported mapped section type: {type_name}")

    # ============================================================
    # HELPERS
    # ============================================================
    def _create_thickness(self, prop, index: int, name: str) -> SectionThickness:

        _, thickness, _= self._split_thickness(name)

        return SectionThickness(
            index=index,
            type_index=3,
            type_name="THICKNESS",
            misc=(0, 0, 0, 0, 0.00, 0.00),
            name=name,
            thickness=thickness,
        )

    def _create_rect(self, prop, index: int, name: str) -> SectionRect:
        # prefix must be B or C
        
        _, width, height, _ = self._split_rect(name)

        return SectionRect(
            index=index,
            type_index=6,
            type_name="RECT",
            misc=(0, 0, 0, 0, 0.00, 0.00),
            name=name,
            width=width,
            height=height,
            slab_thick=0,
        )
    
    def _create_tee(self, prop, index: int, name: str) -> SectionTee:
        # prefix must be B or C
        
        prefix, values, suffix = self._split_tee(name)

        width, height, thick_web, thick_flange = values

        return SectionTee(
            index=index,
            type_index=12,
            type_name="TEE",
            misc=(0, 0, 0, 0, 0.00, 0.00),
            name=name,
            width=width,
            height=height,
            thick_web=thick_web,
            thick_flange=thick_flange,
        )

    def _create_circle(self, prop, index: int, name: str) -> SectionCircle:
        
        _, diameter, _= self._split_thickness(name)

        return SectionCircle(
            index=index,
            type_index=4,
            type_name="CIRCLE",
            misc=(0, 0, 0, 0, 0.0, 0.0),
            name=name,
            diameter=diameter,
        )
    
    def _create_user(self, prop, index: int, name: str) -> SectionCircle:

        return SectionUser(
            index=index,
            type_index=12,
            type_name="USER",
            misc=(0, 0, 0, 0, 0.0, 0.0),
            name=name,
            steel_sect=name,
            strong_axis=True
        )

    # ============================================================
    # BULK CREATION
    # ============================================================
    def create_all(self) -> Sections:
        """
        Create all Section objects from the section_map and section_props.
        """
        sections = [self.create_section(key) for key in self.section_map.keys()]
        return Sections(sections)
    
    # ============================================================
    # BULK CREATION
    # ============================================================
    
    def _split_thickness(self, name: str):
        """
        Split a string into:
            prefix = leading letters
            value  = float number in the middle
            suffix = trailing letters (optional)
        Accepts patterns like:
            S15
            S15A
            FC20
            FC20B
            C200AB
        """
        if not isinstance(name, str):
            raise TypeError(f"Expected string, got {type(name)}")

        # prefix letters + number + optional trailing letters
        m = re.match(r"^([A-Za-z]+)(\d+\.?\d*)([A-Za-z]*)$", name)
        if not m:
            raise ValueError(f"Invalid naming pattern: '{name}'")

        prefix, number_str, suffix = m.groups()
        return prefix, float(number_str), suffix
    
    def _split_rect(self, name: str):
        """
        Parse strings like:
            B15x30A
            B15/30A
            B15-30
            C200_400B
        into:
            prefix, value1, value2, suffix
        """
        if not isinstance(name, str):
            raise TypeError(f"Expected string, got {type(name)}")

        # prefix letters + num1 + separator (any non-letter/digit) + num2 + optional suffix
        m = re.match(
            r"^([A-Za-z]+)(\d+\.?\d*)([xX×/:\-_])(\d+\.?\d*)([A-Za-z]*)$",
            name
        )
        if not m:
            raise ValueError(f"Invalid naming pattern: '{name}'")

        prefix, num1, sep, num2, suffix = m.groups()
        return prefix, float(num1), float(num2), suffix
    
    def _split_tee(self, name: str):
        """
        Parse strings like:
            T30X40X15X25
            T30x30x15x15
            T200/300/50/75A
            C100_200_300B

        Returns:
            prefix: str
            values: list[float]
            suffix: str

        Rules:
        - prefix = leading letters
        - suffix = trailing letters
        - middle = 2+ numeric tokens separated by [xX×/:\-_]
        """
        if not isinstance(name, str):
            raise TypeError(f"Expected string, got {type(name)}")

        m = re.match(
            r"""
            ^([A-Za-z]+)            # prefix letters
            (                       # start numeric block
                \d+\.?\d*           # first number
                (?:[xX×/:\-_]\d+\.?\d*)+   # 1+ (sep + number)
            )
            ([A-Za-z]*)$            # optional suffix
            """,
            name,
            flags=re.VERBOSE,
        )

        if not m:
            raise ValueError(f"Invalid multi-dimension pattern: '{name}'")

        prefix, numblock, suffix = m.groups()

        # split by any separator
        values = [float(v) for v in re.split(r"[xX×/:\-_]", numblock)]

        return prefix, values, suffix
    
class SectionsComparer(CollectionComparer[Model, SectionBase, Sections]):
    """
    Specialized comparer for Section collections.
    Uses type_sort_rules both as:
      - global type ordering (based on definition order)
      - per-type sorting rule within each group
    """

    # ------------------------------------------------------------
    # Parsing Helpers
    # ------------------------------------------------------------
    @staticmethod
    def parse_name_parts(name: str):
        if not name:
            return ("", float("inf"))

        # Extract prefix
        m = re.match(r"([A-Za-z_]+)", name)
        prefix = m.group(1).upper() if m else ""

        # Extract all numbers in order (e.g., 45, 120, 3.5)
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", name)]
        if not nums:
            nums = [float("inf")]

        return (prefix, *nums)

    # ------------------------------------------------------------
    # Type-specific sorting rules
    # ------------------------------------------------------------
    type_sort_rules = {
        SectionThickness: lambda o: (
            *SectionsComparer.parse_name_parts(str(getattr(o, "name", ""))),
            getattr(o, "thickness", float("inf")),
        ),

        SectionRect: lambda o: (
            *SectionsComparer.parse_name_parts(str(getattr(o, "name", ""))),
            getattr(o, "width", float("inf")),
            getattr(o, "height", float("inf")),
        ),

        SectionCircle: lambda o: (
            *SectionsComparer.parse_name_parts(str(getattr(o, "name", ""))),
            getattr(o, "diameter", float("inf")),
        ),
    }

    # ------------------------------------------------------------
    # Core sort key builder
    # ------------------------------------------------------------
    @classmethod
    def get_sort_key(cls, obj):
        obj_type = type(obj)
        type_order = list(cls.type_sort_rules.keys())

        try:
            type_priority = type_order.index(obj_type)
        except ValueError:
            type_priority = len(type_order)

        key_func = cls.type_sort_rules.get(obj_type)
        if key_func:
            return (type_priority, *key_func(obj))
        return (type_priority, float("inf"))