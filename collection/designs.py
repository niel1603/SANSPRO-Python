import re
from typing import Type, List, Dict, Optional
from collections import OrderedDict

from SANSPRO.model.model import Model
from SANSPRO.object.design import (
    FunctionIndex, 
    StructureType, 
    DesignCode,   
    StirrupType,
    DesignConcreteBase,
    ColumnRebarFace, 
    ReinforcedConcrete,
    DesignConcreteSlab, 
    DesignConcreteWall, 
    DesignConcreteGirder, 
    DesignConcreteBiaxialColumn, 
    DesignConcreteCircularColumn,

    )

from SANSPRO.object.design import (
    SectionOption,
    CompositeOption,
    SteelDesignBase,
    )

from SANSPRO.object.material import MaterialBase, MaterialIsotropic
from SANSPRO.object.design import DesignConcreteBase

from SANSPRO.collection.materials import Materials
from SANSPRO.collection.sections import Sections

from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

from compact.elset.section_properties import (
    SectionPropertyBase,
    SectionPropertyConcreteSlab,
    SectionPropertyConcreteBeam, 
    SectionPropertyConcreteBiaxialColumn, 
    SectionPropertyConcreteCircularColumn,
    SectionPropertyConcreteWall, 
    )


from SANSPRO.variable.parameter import ParameterParse, ParameterAdapter

class Designs(Collection[DesignConcreteBase]):
    header = 'DESIGN'

class DesignsParse(CollectionParser[Model, DesignConcreteBase, Designs]):
    LINES_PER_ITEM = 3

    @classmethod
    def get_collection(cls) -> Type[Designs]:
        return Designs

    @classmethod
    def parse_line(cls, lines: List[str], sections: Sections) -> DesignConcreteBase:
        tokens = [line.split() for line in lines]
        section_type = tokens[0][2].upper()

        if section_type == "CONCRETE_SLAB":
            return cls._parse_concrete_slab(tokens, sections)
        elif section_type == "CONCRETE_WALL":
            return cls._parse_concrete_wall(tokens, sections)
        elif section_type == "CONCRETE_GIRDER":
            return cls._parse_concrete_girder(tokens, sections)
        elif section_type == "CONCRETE_BCOL":
            return cls._parse_concrete_biaxial_column(tokens, sections)
        elif section_type == "CONCRETE_CCOL":
            return cls._parse_concrete_circular_column(tokens, sections)
        elif section_type == "STEEL_FRAME":
            return cls._parse_steel_frame(tokens, sections)
        else:
            # skip unknown section types
            print(f"[WARN] Skipping unsupported DESIGN type: {section_type}")
            return None

    @staticmethod
    def _parse_concrete_base(tokens: List[List[str]], sections: Sections) -> Dict:
        l0, l1, l2 = tokens

        index = int(l0[0])
        name = str(l0[3])

        # --- 🔹 Use section name if available ---
        if sections is not None:
            section = sections.get(index)
            if section is None:
                print(f"[WARN] No matching Section index {index} for Design '{name}'")
            else:
                if section.name != name:
                    print(f"[NOTICE] Design[{index}] name '{name}' replaced with Section name '{section.name}'")
                name = section.name  # authoritative source

        # --- Shared: Reinforced concrete material ---
        rc = ReinforcedConcrete(
            ec=float(l2[7]),
            fc1=float(l2[8]),
            fci=float(l2[9]),
            fcr=float(l2[10]),
            fy=float(l2[11]),
            db=float(l2[12]),
            delta=float(l2[13]),
            column_rebar_faces=ColumnRebarFace(int(l2[14])),
            fys=float(l2[15]),
            dbs=float(l2[16]),
            nside=float(l2[17]),
            sidebar_space=float(l2[18]),
            stirrup_types=bool(int(l2[19])),
            fyv=float(l2[20]),
            dbv=float(l2[21]),
            stirrup_space_max=float(l2[22]),
            hollow_section=bool(int(l2[23])),
            tcc=float(l2[24]),
            tcf=float(l2[25]),
        )

        base = dict(
            index=index,
            type_index=int(l0[1]),
            type_name=str(l0[2]),
            name=name,
            function_index=FunctionIndex(int(l0[4])),
            structure_type=StructureType(int(l0[5])),
            design_code=DesignCode(int(l0[6])),
            compute_k=bool(int(l0[7])),
            show_detail=bool(int(l0[8])),
            show_diagram=bool(int(l0[9])),
            use_global_load_factor=bool(int(l0[10])),

            phi_flexure=float(l1[0]),
            phit_flex_tens=float(l1[1]),
            phi_flex_comp=float(l1[2]),
            phi_flex_comp_spiral=float(l1[3]),
            phi_shear=float(l1[4]),
            phi_torsion=float(l1[5]),
            phi_bearing=float(l1[6]),
            phi_connection=float(l1[7]),

            k_x=float(l1[8]),
            k_y=float(l1[9]),
            l_u=float(l1[10]),
            l_ux=float(l1[11]),
            l_uy=float(l1[12]),

            c_mx=float(l1[13]),
            c_my=float(l1[14]),
            cb=float(l1[15]),

            gravity_load_reduction=float(l1[16]),
            earthquake_load_reduction=float(l1[17]),

            reinforced_concrete=rc,
        )
        return base
    
    @staticmethod
    def _parse_steel_base(tokens: List[List[str]], sections: Sections) -> Dict:
        l0, l1, l2 = tokens

        index = int(l0[0])
        name = str(l0[3])

        # --- 🔹 Use section name if available ---
        if sections is not None:
            section = sections.get(index)
            if section is None:
                print(f"[WARN] No matching Section index {index} for Design '{name}'")
            else:
                if section.name != name:
                    print(f"[NOTICE] Design[{index}] name '{name}' replaced with Section name '{section.name}'")
                name = section.name  # authoritative source

        # --- Shared: Reinforced concrete material ---
        base = dict(
            index=index,
            type_index=int(l0[1]),
            type_name=str(l0[2]),
            name=name,
            function_index=FunctionIndex(int(l0[4])),
            structure_type=StructureType(int(l0[5])),
            design_code=DesignCode(int(l0[6])),
            compute_k=bool(int(l0[7])),
            show_detail=bool(int(l0[8])),
            show_diagram=bool(int(l0[9])),
            use_global_load_factor=bool(int(l0[10])),

            phi_flexure=float(l1[0]),
            phit_flex_tens=float(l1[1]),
            phi_flex_comp=float(l1[2]),
            phi_flex_comp_spiral=float(l1[3]),
            phi_shear=float(l1[4]),
            phi_torsion=float(l1[5]),
            phi_bearing=float(l1[6]),
            phi_connection=float(l1[7]),

            k_x=float(l1[8]),
            k_y=float(l1[9]),
            l_u=float(l1[10]),
            l_ux=float(l1[11]),
            l_uy=float(l1[12]),

            c_mx=float(l1[13]),
            c_my=float(l1[14]),
            cb=float(l1[15]),

            gravity_load_reduction=float(l1[16]),
            earthquake_load_reduction=float(l1[17]),
        )
        return base

    @staticmethod
    def _parse_concrete_slab(tokens: List[List[str]], sections: Sections) -> DesignConcreteSlab:
        l0, l1, l2 = tokens
        base = DesignsParse._parse_concrete_base(tokens, sections)
        return DesignConcreteSlab(**base, tp=float(l2[2]), cv=float(l2[6]))

    @staticmethod
    def _parse_concrete_wall(tokens: List[List[str]], sections: Sections) -> DesignConcreteWall:
        l0, l1, l2 = tokens
        base = DesignsParse._parse_concrete_base(tokens, sections)
        return DesignConcreteWall(**base, tp=float(l2[2]), cv=float(l2[6]))

    @staticmethod
    def _parse_concrete_girder(tokens: List[List[str]], sections: Sections) -> DesignConcreteGirder:
        l0, l1, l2 = tokens
        base = DesignsParse._parse_concrete_base(tokens, sections)
        return DesignConcreteGirder(
            **base,
            bw=float(l2[2]),
            ht=float(l2[3]),
            bf=float(l2[4]),
            tf=float(l2[5]),
            cv=float(l2[6]),
        )
    
    @staticmethod
    def _parse_concrete_biaxial_column(tokens: List[List[str]], sections: Sections) -> DesignConcreteBiaxialColumn:
        l0, l1, l2 = tokens
        base = DesignsParse._parse_concrete_base(tokens, sections)
        return DesignConcreteBiaxialColumn(
            **base,
            b=float(l2[2]),
            h=float(l2[3]),
            bf=float(l2[4]),
            tf=float(l2[5]),
            cv=float(l2[6]),
        )

    @staticmethod
    def _parse_concrete_circular_column(tokens: List[List[str]], sections: Sections) -> DesignConcreteCircularColumn:
        l0, l1, l2 = tokens
        base = DesignsParse._parse_concrete_base(tokens, sections)
        return DesignConcreteCircularColumn(
            **base,
            d=float(l2[2]),
            cv=float(l2[6]),
        )
    
    @staticmethod
    def _parse_steel_frame(tokens: List[List[str]], sections: Sections) -> SteelDesignBase:
        l0, l1, l2 = tokens
        base = DesignsParse._parse_steel_base(tokens, sections)
        return SteelDesignBase(
            **base,
            section_option= SectionOption(int(l2[2])),
            composite_option= CompositeOption(int(l2[3])),
            connection_design= bool((int(l2[4]))),

            section= str(l2[5]),
            wf2= str(l2[6]),
            strong_axis= bool(l2[7]),
            h1_ho= int(l2[8]),
            space= int(l2[9]),

            Es= float(l2[10]),
            Fu= float(l2[11]),
            Fy= float(l2[12]),

            Ag= float(l2[13]),
            Rmin= float(l2[14]),
            Wx= float(l2[15]),
            Wy= float(l2[16]),
            An_Ag= float(l2[17]),
            material_name= str(l2[18]),

            left_haunch_length= float(l2[19]),
            left_haunch_height= float(l2[20]),

            right_haunch_length= float(l2[21]),
            right_haunch_height= float(l2[22]),

            Tu= float(l2[23]),
            Ty= float(l2[24]),

            tension_only= bool(l2[25]),

            Ry= float(l2[26]),
            Rt= float(l2[27]),
        )
    # ==========================================================
    # from_model — add validation with Sections
    # ==========================================================
    @classmethod
    def from_model(cls, model: Model, sections:Sections) -> 'Designs':
        collection_cls = cls.get_collection()
        block = model.blocks.get(collection_cls.header)
        parsed_items: list[DesignConcreteBase] = []

        n = getattr(cls, "LINES_PER_ITEM", 1)
        lines = block.body

        for i in range(0, len(lines), n):
            item_lines = lines[i:i + n]
            try:
                parsed_item = cls.parse_line(item_lines, sections=sections)
            except Exception:
                import traceback; traceback.print_exc()
                parsed_item = None

            if parsed_item:
                parsed_items.append(parsed_item)

        return collection_cls(parsed_items)

class DesignsAdapter(ObjectCollectionAdapter[Model, DesignConcreteBase, Designs]):

    @classmethod
    def update_var(cls, designs: Designs, model: Model) -> Model:

        parameter = ParameterParse.from_mdl(model)
        parameter.design_data = len(designs.objects)
        model = ParameterAdapter.to_model(parameter, model)

        return model

    @classmethod
    def format_line(cls, design: DesignConcreteBase) -> str:

        if design.type_name == "CONCRETE_SLAB":
            return cls._format_line_slab(design)
        elif design.type_name == "CONCRETE_WALL":
            return cls._format_line_wall(design)
        elif design.type_name == "CONCRETE_GIRDER":
            return cls._format_line_girder(design)
        elif design.type_name == "CONCRETE_BCOL":
            return cls._format_line_bcol(design)
        elif design.type_name == "CONCRETE_CCOL":
            return cls._format_line_ccol(design)
        else:
            print(f"[WARN] Skipping unsupported DESIGN type: {design.type_name}")
            return None
    
    @classmethod
    def _format_line_base(cls, d: DesignConcreteBase) -> str:

        i = int(d.index)
        t_i = int(d.type_index)
        t_n = str(d.type_name)
        n = str(d.name)

        f_i = int(d.function_index)
        s_t = int(d.structure_type)
        d_c = int(d.design_code)

        c_k = int(d.compute_k)
        s_de = int(d.show_detail)
        s_di = int(d.show_diagram)
        u_g = int(d.use_global_load_factor)

        # phi
        p_f   = cls._norm_float(d.phi_flexure)
        p_tf  = cls._norm_float(d.phit_flex_tens)
        p_fc  = cls._norm_float(d.phi_flex_comp)
        p_fcs = cls._norm_float(d.phi_flex_comp_spiral)
        p_sh  = cls._norm_float(d.phi_shear)
        p_tr  = cls._norm_float(d.phi_torsion)
        p_br  = cls._norm_float(d.phi_bearing)
        p_cn  = cls._norm_float(d.phi_connection)

        # length factors
        k_x  = cls._norm_float(d.k_x)
        k_y  = cls._norm_float(d.k_y)
        l_u  = cls._norm_float(d.l_u)
        l_ux = cls._norm_float(d.l_ux)
        l_uy = cls._norm_float(d.l_uy)

        # Moment multiplier
        c_mx = cls._norm_float(d.c_mx)
        c_my = cls._norm_float(d.c_my)
        cb   = cls._norm_float(d.cb)

        # Live load reduction
        g_lr = cls._norm_float(d.gravity_load_reduction)
        e_lr = cls._norm_float(d.earthquake_load_reduction)

        cv   = cls._norm_float(d.cv)

        line1 = f'{i:>4}{t_i:>4} {t_n:<12} {n} {f_i} {s_t} {d_c} {c_k} {s_de} {s_di} {u_g}'
        line2 = f'      {p_f} {p_tf} {p_fc} {p_fcs} {p_sh} {p_tr} {p_br} {p_cn}   {k_x} {k_y} {l_u} {l_ux} {l_uy}   {c_mx} {c_my} {cb} {g_lr} {e_lr}'

        return line1, line2, cv

    @classmethod
    def _format_line_reinforced(cls, d: DesignConcreteBase, section_properties_line: str) -> str:

        rc = d.reinforced_concrete

        sp_l = section_properties_line

        # concrete
        ec  = cls._norm_float(rc.ec)
        fc1 = cls._norm_float(rc.fc1)
        fci = cls._norm_float(rc.fci)
        fcr = cls._norm_float(rc.fcr)

        # main_rebar
        fy   = cls._norm_float(rc.fy)
        db   = cls._norm_float(rc.db)
        dlt  = cls._norm_float(rc.delta)
        crf  = int(rc.column_rebar_faces)

        # side_rebar
        fys   = cls._norm_float(rc.fys)
        dbs   = cls._norm_float(rc.dbs)
        nside = cls._norm_float(rc.nside)
        sb_s  = cls._norm_float(rc.sidebar_space)

        # stirrup
        st_tp = int(rc.stirrup_types)
        fyv   = cls._norm_float(rc.fyv)
        dbv   = cls._norm_float(rc.dbv)
        st_sm = cls._norm_float(rc.stirrup_space_max)

        # hollow
        hllw = int(rc.hollow_section)
        tcc  = cls._norm_float(rc.tcc)
        tcf  = cls._norm_float(rc.tcf)


        line3 = f'      CONCRETE = {sp_l}  {ec} {fc1} {fci} {fcr}  {fy} {db} {dlt} {crf}  {fys} {dbs} {nside} {sb_s}  {st_tp} {fyv} {dbv} {st_sm}  {hllw} {tcc} {tcf}'
        return line3

    @classmethod
    def _format_line_slab(cls, d: DesignConcreteSlab) -> str:
        line1, line2, cv = cls._format_line_base(d)

        tp = cls._norm_float(d.tp)
        section_properties_line = f'{tp} 0 0 0 {cv}'
        
        line3 = cls._format_line_reinforced(d, section_properties_line)
        line = f'{line1}\n{line2}\n{line3}'

        return line
    
    @classmethod
    def _format_line_wall(cls, d: DesignConcreteWall) -> str:
        line1, line2, cv = cls._format_line_base(d)

        tp = cls._norm_float(d.tp)
        section_properties_line = f'{tp} 0 0 0 {cv}'
        
        line3 = cls._format_line_reinforced(d, section_properties_line)
        line = f'{line1}\n{line2}\n{line3}'

        return line
    
    @classmethod
    def _format_line_girder(cls, d: DesignConcreteGirder) -> str:
        line1, line2, cv = cls._format_line_base(d)

        bw = cls._norm_float(d.bw)
        ht = cls._norm_float(d.ht)
        bf = cls._norm_float(d.bf)
        tf = cls._norm_float(d.tf)

        section_properties_line = f'{bw} {ht} {bf} {tf} {cv}'
        
        line3 = cls._format_line_reinforced(d, section_properties_line)
        line = f'{line1}\n{line2}\n{line3}'

        return line
    
    @classmethod
    def _format_line_bcol(cls, d: DesignConcreteBiaxialColumn) -> str:
        line1, line2, cv = cls._format_line_base(d)

        b = cls._norm_float(d.b)
        h = cls._norm_float(d.h)
        bf = cls._norm_float(d.bf)
        tf = cls._norm_float(d.tf)
        
        section_properties_line = f'{b} {h} {bf} {tf} {cv}'
        
        line3 = cls._format_line_reinforced(d, section_properties_line)
        line = f'{line1}\n{line2}\n{line3}'

        return line
    
    @classmethod
    def _format_line_ccol(cls, d: DesignConcreteCircularColumn) -> str:
        line1, line2, cv = cls._format_line_base(d)

        dia = cls._norm_float(d.d)
        section_properties_line = f'{dia} 0 0 0 {cv}'
        
        line3 = cls._format_line_reinforced(d, section_properties_line)
        line = f'{line1}\n{line2}\n{line3}'

        return line
    
class DesignFactory:
    """
    Factory that builds DesignBase objects from a design_map and section property instances.
    Uses class-based type mapping (no reliance on section_property_type strings).
    """

    TYPE_MAP: Dict[Type[SectionPropertyBase], Type[DesignConcreteBase]] = {
        SectionPropertyConcreteSlab: DesignConcreteSlab,
        SectionPropertyConcreteWall: DesignConcreteWall,
        SectionPropertyConcreteBeam: DesignConcreteGirder,
        SectionPropertyConcreteBiaxialColumn: DesignConcreteBiaxialColumn,
        SectionPropertyConcreteCircularColumn: DesignConcreteCircularColumn,
    }

    FUNCTION_MAP: Dict[Type[DesignConcreteBase], FunctionIndex] = {
        DesignConcreteSlab: FunctionIndex.SLAB,
        DesignConcreteWall: FunctionIndex.SHEAR_WALL,
        DesignConcreteGirder: FunctionIndex.BEAM,
        DesignConcreteBiaxialColumn: FunctionIndex.COLUMN,
        DesignConcreteCircularColumn: FunctionIndex.COLUMN,
    }

    def __init__(
        self,
        design_map: "OrderedDict[tuple, int]",
        design_props: Dict[int, SectionPropertyBase],
        material_map: "OrderedDict[str, int]",
        materials: "Materials",
        sections: "Sections",
    ):
        self.design_map = design_map
        self.design_props = design_props
        self.material_map = material_map
        self.materials = materials
        self.sections = sections

    # ============================================================
    # MAIN ENTRY
    # ============================================================
    def create_design(self, design_key: tuple) -> DesignConcreteBase:
        if design_key not in self.design_map:
            raise KeyError(f"Design key {design_key} not found")

        index = self.design_map[design_key]
        section_prop = self.design_props[index]

        design_cls = self.TYPE_MAP[type(section_prop)]
        name = section_prop.name

        # infer function type
        fn = self.FUNCTION_MAP[design_cls]

        # resolve material (NEW — use SectionProperty)
        material = self._get_material(section_prop)

        section = self.sections.get_by_name(name)
        
        # build RC

        base = dict(
            index=index,
            name=name,
            function_index=fn,
            structure_type=StructureType.DUCTILE,
            design_code=DesignCode.CONCRETE_ACI_2014,

            # booleans
            compute_k=True,
            show_detail=True,
            show_diagram=True,
            use_global_load_factor=False,

            # phi factors
            phi_flexure=0.9,
            phit_flex_tens=0.9,
            phi_flex_comp=0.65,
            phi_flex_comp_spiral=0.75,
            phi_shear=0.75,
            phi_torsion=0.75,
            phi_bearing=0.65,
            phi_connection=1.0,

            # k and length factors
            k_x=1.0,
            k_y=1.0,
            l_u=1.0,
            l_ux=1.0,
            l_uy=1.0,

            # moment magnification
            c_mx=1.0,
            c_my=1.0,
            cb=1.0,

            # load reduction
            gravity_load_reduction=1.0,
            earthquake_load_reduction=1.0,
            
        )

        # ---------- type-specific ----------
        if design_cls is DesignConcreteSlab:

            name = section_prop.name

            thickness = section.thickness
            
            rc = self._build_reinforced_concrete(section_prop=section_prop, material=material)

            return DesignConcreteSlab(
                **base,
                type_index=8,
                type_name="CONCRETE_SLAB",
                tp=thickness,
                cv=section_prop.rc.cover,
                reinforced_concrete=rc,
            )

        if design_cls is DesignConcreteWall:

            name = section_prop.name
            
            rc = self._build_reinforced_concrete(section_prop=section_prop, material=material)
            
            return DesignConcreteWall(
                **base,
                type_index=9,
                type_name="CONCRETE_WALL",
                tp=thickness,
                cv=section_prop.rc.cover,
                reinforced_concrete=rc,
            )

        if design_cls is DesignConcreteGirder:

            name = section_prop.name

            width=section.width
            height=section.height
            
            rc = self._build_reinforced_concrete(section_prop=section_prop, material=material, depth=height)
            
            return DesignConcreteGirder(
                **base,
                type_index=4,
                type_name="CONCRETE_GIRDER",
                bw=width,
                ht=height,
                bf=width,
                tf=0,
                cv=section_prop.rc.cover,
                reinforced_concrete=rc,
            )

        if design_cls is DesignConcreteBiaxialColumn:

            name = section_prop.name

            width=section.width
            height=section.height
            
            rc = self._build_reinforced_concrete(section_prop=section_prop, material=material)
            
            return DesignConcreteBiaxialColumn(
                **base,
                type_index=7,
                type_name="CONCRETE_BCOL",
                b=width,
                h=height,
                bf=width,
                tf=0,
                cv=section_prop.rc.cover,
                reinforced_concrete=rc,
            )

        if design_cls is DesignConcreteCircularColumn:
            
            name = section_prop.name

            diameter = section.diameter
            
            rc = self._build_reinforced_concrete(section_prop=section_prop, material=material)
        
            return DesignConcreteCircularColumn(
                **base,
                type_index=5,
                type_name="CONCRETE_CCOL",
                d=section.diameter,
                cv=section_prop.rc.cover,
                reinforced_concrete=rc,
            )

        raise ValueError(f"Unhandled design class {design_cls}")

    # ============================================================
    # HELPERS
    # ============================================================

    def _infer_function_index(self, design_cls: Type[DesignConcreteBase]) -> FunctionIndex:
        """
        Infer FunctionIndex from the design class using FUNCTION_MAP.
        """
        return self.FUNCTION_MAP.get(design_cls, FunctionIndex.GENERAL)
    
    def _get_material(self, section_prop: SectionPropertyBase) -> MaterialBase:
        mat_name = section_prop.material   # actual name string
        mat_index = self.material_map.get(mat_name)

        if mat_index is None:
            raise KeyError(f"Material name '{mat_name}' not found in material_map")

        mat = self.materials.get(mat_index)
        if mat is None:
            raise KeyError(f"Material index {mat_index} not found in Materials")

        return mat
    
    def _build_reinforced_concrete(
        self,
        section_prop: SectionPropertyBase,
        material: MaterialIsotropic,
        depth: Optional[float] = None,
    ) -> ReinforcedConcrete:
        

        fc1 = material.fc1

        ec = material.elastic_mod
        fci = 0.45 * fc1
        fcr = 0.2 * fc1

        rc_prop = section_prop.rc

        # --- Delta selection based on section type ---
        if isinstance(section_prop, SectionPropertyConcreteSlab):
            delta = 0.4
            column_rebar_faces=ColumnRebarFace.TWO_FACES
            
            nside = 0
            sidebar_space=30
            
            stirrup_type = StirrupType.RECTANGLE
        elif isinstance(section_prop, SectionPropertyConcreteWall):
            delta = 1
            column_rebar_faces=ColumnRebarFace.TWO_FACES
            
            nside = 0
            sidebar_space=30

            stirrup_type = StirrupType.RECTANGLE
        elif isinstance(section_prop, SectionPropertyConcreteBeam):
            delta = 0.5
            column_rebar_faces=ColumnRebarFace.TWO_FACES

            sidebar_space=30
            nside = round((depth / sidebar_space - 1), 0) * 2
            
            stirrup_type = StirrupType.RECTANGLE

        elif isinstance(section_prop, SectionPropertyConcreteBiaxialColumn):
            delta = 1
            column_rebar_faces=ColumnRebarFace.FOUR_FACES

            nside = 0
            sidebar_space=30

            stirrup_type = StirrupType.RECTANGLE
        elif isinstance(section_prop, SectionPropertyConcreteCircularColumn):
            delta = 1
            column_rebar_faces=ColumnRebarFace.FOUR_FACES

            nside = 0
            sidebar_space=30

            stirrup_type = StirrupType.SPIRAL
        else:
            raise TypeError(
                f"Unsupported SectionProperty type '{type(section_prop).__name__}' "
                f"for ReinforcedConcrete construction."
            )
        
        def _determine_fy_from_db(db: float) -> float:
            return 2400.0 if db < 1 else 4200.0

        db  = rc_prop.bar_dim
        dbs = rc_prop.tie_dim
        dbv = rc_prop.tie_dim

        fy  = _determine_fy_from_db(db)
        fys = _determine_fy_from_db(dbs)
        fyv = _determine_fy_from_db(dbv)


        return ReinforcedConcrete(
            ec=ec,
            fc1=fc1,
            fci=fci,
            fcr=fcr,
            fy=fy,
            db=db,
            delta=delta,
            column_rebar_faces=column_rebar_faces,
            fys=fys,
            dbs=dbs,
            nside=nside,
            sidebar_space=sidebar_space,
            stirrup_types=stirrup_type,
            fyv=fyv,
            dbv=dbv,
            stirrup_space_max=30,
            hollow_section=False,
            tcc=0.0,
            tcf=0.0,
        )

    # ============================================================
    # BULK CREATION
    # ============================================================
    def create_all(self) -> Designs:
        """
        Build a full Designs collection from all entries in design_map.
        """
        designs: list[DesignConcreteBase] = [
            self.create_design(key) for key in self.design_map.keys()
        ]
        return Designs(designs)
    
class DesignsComparer(CollectionComparer["Model", DesignConcreteBase, "Designs"]):
    """
    Specialized comparer for Design collections.
    Uses type_sort_rules both as:
      - global type ordering (based on definition order)
      - per-type sorting rule within each group
    """

    # ------------------------------------------------------------
    # Parsing Helpers
    # ------------------------------------------------------------
    @staticmethod
    def _parse_name_parts(name: str):
        """
        Extract prefix, all numeric values, and optional trailing suffix.
        
        Examples:
            'TP10'          → ('TP', [10], '')
            'B15/20A'       → ('B', [15, 20], 'A')
            'K45/120/3.5Z'  → ('K', [45, 120, 3.5], 'Z')
            'RECT_200X400'  → ('RECT', [200, 400], '')
            'C300'          → ('C', [300], '')
        """

        if not name:
            return ("", [float("inf")], "")

        # --- prefix: leading letters or underscores ---
        m = re.match(r"([A-Za-z_]+)", name)
        prefix = m.group(1).upper() if m else ""

        # --- extract all numbers ---
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", name)]
        if not nums:
            nums = [float("inf")]

        # --- extract optional trailing suffix (letters after last number) ---
        m_suffix = re.search(r"\d(?:[^\d]*?)([A-Za-z]+)$", name)
        suffix = m_suffix.group(1) if m_suffix else ""

        return (prefix, nums, suffix)
    
    @staticmethod
    def _name_sort_key(obj):
        prefix, nums, suffix = DesignsComparer._parse_name_parts(str(getattr(obj, "name", "")))
        return (prefix, *nums, suffix)

    # ------------------------------------------------------------
    # Type-specific sorting rules
    # ------------------------------------------------------------

    type_sort_rules = {
        DesignConcreteSlab: lambda o: (
            *DesignsComparer._name_sort_key(o),
            getattr(o, "tp", float("inf")),
        ),

        DesignConcreteGirder: lambda o: (
            *DesignsComparer._name_sort_key(o),
            getattr(o, "bw", float("inf")),
            getattr(o, "ht", float("inf")),
        ),

        DesignConcreteBiaxialColumn: lambda o: (
            *DesignsComparer._name_sort_key(o),
            getattr(o, "b", float("inf")),
            getattr(o, "h", float("inf")),
        ),

        DesignConcreteCircularColumn: lambda o: (
            *DesignsComparer._name_sort_key(o),
            getattr(o, "d", float("inf")),
        ),

        DesignConcreteWall: lambda o: (
            *DesignsComparer._name_sort_key(o),
            getattr(o, "tp", float("inf")),
        ),
    }

    # ------------------------------------------------------------
    # Core sort key builder
    # ------------------------------------------------------------
    @classmethod
    def get_sort_key(cls, obj):
        """
        Sorting priority:
        1. Type order = order in type_sort_rules
        2. Per-type rule defined in type_sort_rules
        """
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