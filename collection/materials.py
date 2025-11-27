import re
from typing import Dict, Type, List, Tuple

from SANSPRO.model.model import Model
from SANSPRO.object.material import MaterialBase, MaterialIsotropic, MaterialSpring
from collection._collection_abstract import (
    Collection, 
    CollectionParser, 
    ObjectCollectionQuery, 
    ObjectCollectionEngine, 
    ObjectCollectionAdapter, 
    CollectionComparer)

from SANSPRO.variable.parameter import ParameterParse, ParameterAdapter

class Materials(Collection[MaterialBase]):
    header = 'MATERIAL'

class MaterialsParse(CollectionParser[Model, MaterialBase, Materials]):
    LINES_PER_ITEM = 2

    @classmethod
    def get_collection(cls) -> Type[Materials]:
        return Materials

    @classmethod
    def parse_line(cls, lines: List[str]) -> MaterialBase:
        tokens = [line.split() for line in lines]
        material_type = tokens[0][2].upper()

        if material_type == "ISOTROPIC":
            return cls._parse_isotropic(tokens)
        elif material_type == "SPRING":
            return cls._parse_spring(tokens)
        else:
            # skip unknown section types
            print(f"[WARN] Skipping unsupported MATERIAL type: {material_type}")
            return None
        
    @staticmethod
    def _parse_material_base(tokens: List[List[str]]) -> Dict:
        l0, l1= tokens

        # --- Shared: DesignBase parameters ---
        base = dict(
            index=int(l0[0]),
            type_index=int(l0[1]),
            type_name=str(l0[2]),
            name=str(l0[3]),

            misc1 = (
            int(l0[4]),
            int(l0[5]),
            int(l0[6]),
            int(l0[7]),
            )
        )

        return base

    @staticmethod
    def _parse_isotropic(tokens: List[List[str]]) -> MaterialIsotropic:
        l0, l1 = tokens
        base = MaterialsParse._parse_material_base(tokens)

        material_isotropic = MaterialIsotropic(
            **base,
            fc1=float(l0[8]),
            time_dependent=bool(int(l0[9])),
            alpha=float(l0[10]),
            beta=float(l0[11]),

            misc2=int(l1[0]),
            thermal_coeficient=float(l1[1]),
            unit_weight=float(l1[2]),
            elastic_mod=float(l1[3]),
            shear_mod=float(l1[4]),
            poisson_ratio=float(l1[5]),
        )
        return material_isotropic
    
    @staticmethod
    def _parse_spring(tokens: List[List[str]]) -> MaterialSpring:
        l0, l1 = tokens
        base = MaterialsParse._parse_material_base(tokens)

        material_spring = MaterialSpring(
            **base,

            misc2=int(l1[0]),
            spring_stiff=float(l1[3]),
            spring_min=float(l1[4]),
            spring_max=float(l1[5]),
        )
        return material_spring
    
class MaterialsAdapter(ObjectCollectionAdapter[Model, MaterialBase, Materials]):

    @classmethod
    def update_var(cls, materials: Materials, model: Model) -> Model:

        parameter = ParameterParse.from_mdl(model)
        parameter.material_properties = len(materials.objects)
        model = ParameterAdapter.to_model(parameter, model)

        return model

    @classmethod
    def format_line(cls, material: MaterialBase) -> str:

        if material.type_name == "ISOTROPIC":
            return cls._format_line_isotropic(material)
        elif material.type_name == "SPRING":
            return cls._format_line_spring(material)
        else:
            print(f"[WARN] Skipping unsupported MATERIAL type: {material.type_name}")
            return None
    
    @classmethod
    def _format_line_isotropic(cls, m: MaterialIsotropic) -> str:

        i = int(m.index)
        t_i = int(m.type_index)
        t_n = str(m.type_name)
        n = str(m.name)

        m1_0, m1_1, m1_2, m1_3 = m.misc1
        m1_0 = int(m1_0)
        m1_1 = int(m1_1)
        m1_2 = int(m1_2)
        m1_3 = int(m1_3)

        fc1 = cls._norm_float(m.fc1)
        t_d = int(m.time_dependent)
        a = float(m.alpha)
        b = float(m.beta)

        m2 = int(m.misc2)

        t_c = cls._norm_float_sci(float(m.thermal_coeficient))
        u_w = float(m.unit_weight)
        e_m = float(m.elastic_mod)
        s_m = float(m.shear_mod)
        p_r = float(m.poisson_ratio)

        line1 = f'{i:>4}  {t_i} {t_n} {n} {m1_0} {m1_0} {m1_0} {m1_0}  {fc1:>7.2f} {t_d}  {a:.3f}  {b:.3f}'
        line2 = f'{m2:>7} {t_c} {u_w} {e_m} {s_m} {p_r}'

        line = f'{line1}\n{line2}'
        return line
    
    @classmethod
    def _format_line_spring(cls, m: MaterialSpring) -> str:

        i = int(m.index)
        t_i = int(m.type_index)
        t_n = str(m.type_name)
        n = str(m.name)

        m1_0, m1_1, m1_2, m1_3 = m.misc1
        m1_0 = int(m1_0)
        m1_1 = int(m1_1)
        m1_2 = int(m1_2)
        m1_3 = int(m1_3)

        fc1 = 0.00
        t_d = 0
        a = 0.000
        b = 0.000

        m2 = int(m.misc2)

        t_c = 0
        u_w = 0
        s_s = cls._norm_float(m.spring_stiff)
        s_min = cls._norm_float(m.spring_min)
        s_max = cls._norm_float(m.spring_max)

        line1 = f'{i:>4}  {t_i} {t_n} {n} {m1_0} {m1_0} {m1_0} {m1_0}  {fc1:>7.2f} {t_d}  {a:.3f}  {b:.3f}'
        line2 = f'{m2:>7} {t_c} {u_w} {s_s} {s_min} {s_max}'

        line = f'{line1}\n{line2}'
        return line
    
class MaterialsFactory:
    """
    Factory that builds default Material instances from a material_map (name -> index).
    """
    def __init__(self, material_map: Dict[str, int]):
        self.name_to_index = material_map

    def create_material(self, name: str) -> MaterialBase:
        """
        Create a Material instance from its name using the material_map.
        """
        if name not in self.name_to_index:
            raise KeyError(f"Material name '{name}' not found in material_map")

        index = self.name_to_index[name]
        type_name = self._infer_type_from_name(name)

        if type_name == "ISOTROPIC":

            _, fc1 = self._split_isotropic(name)

            fc1_kgcm = fc1 * 10 # conver MPa to kg/cm2

            # Empirical elastic modulus
            elastic_mod = ( 4700 * (fc1 ** 0.5) )
            elastic_mod_kgcm = elastic_mod * 1/9.81 * 100 # conver MPa to kg/cm2
            elastic_mod_kgcm = round(elastic_mod_kgcm, 1)

            poisson_ratio = 0.2
            shear_mod = elastic_mod_kgcm / (2 * (1 + poisson_ratio))
            shear_mod = round(shear_mod, 1)

            return MaterialIsotropic(
                index=index,
                type_index=1,
                type_name=type_name,
                name=name,
                misc1=(0, 0, 0, 0),

                fc1=fc1_kgcm,
                time_dependent=False,
                alpha=0.0,
                beta=0.0,
                misc2=0,

                thermal_coeficient=1e-05,
                unit_weight=0.0024,
                elastic_mod=elastic_mod_kgcm,
                shear_mod=shear_mod,
                poisson_ratio=poisson_ratio,
            )

        elif type_name == "SPRING":
            spring_stiff = float(name.split("-")[-1])

            return MaterialSpring(
                index=index,
                type_index=3,
                type_name=type_name,
                name=name,
                misc1=(0, 0, 0, 0),

                misc2=0,
                spring_stiff=spring_stiff,
                spring_min=0.0,
                spring_max=0.0,
            )

        else:
            raise ValueError(f"Unsupported material type: {type_name}")

    @staticmethod
    def _infer_type_from_name(name: str) -> str:
        name = name.lower()
        if name.startswith("spr "):
            return "SPRING"
        if name.startswith("fc"):
            return "ISOTROPIC"
        raise KeyError(f"Cannot infer type from name '{name}'")
    
    @staticmethod
    def _split_isotropic(name: str):
        m = re.match(r"^([A-Za-z]+)(\d+\.?\d*)$", name)
        if not m:
            raise ValueError(f"Invalid format for prefix+value: '{name}'")
        prefix, num = m.groups()
        return prefix, float(num)

    def create_all(self) -> "Materials":
        """
        Create a Materials collection from all entries in the name→index map.
        """
        materials = [self.create_material(name) for name in self.name_to_index.keys()]
        return Materials(materials)
    
class MaterialsComparer(CollectionComparer[Model, MaterialBase, Materials]):
    """
    Specialized comparer for Material collections.
    Orders first by material class type (MaterialIsotropic → MaterialSpring),
    then by fc1 or name.
    """

    type_order = [
        MaterialIsotropic,
        MaterialSpring,
    ]

    @classmethod
    def get_sort_key(cls, obj):
        obj_type = type(obj)
        try:
            type_priority = cls.type_order.index(obj_type)
        except ValueError:
            # Not found in type_order → put at end
            type_priority = len(cls.type_order)

        if hasattr(obj, "fc1"):
            return (type_priority, float(obj.fc1))
        elif hasattr(obj, "name"):
            return (type_priority, str(obj.name).lower())
        return (type_priority, float("inf"))
