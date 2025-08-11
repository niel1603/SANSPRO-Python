import re
from typing import ClassVar, Dict, List, Union, Tuple, Any
from dataclasses import dataclass, fields, field
from Model.Model import Block, Model, BlockAdapter
from Variable.VariableAbstract import Variable, VariableParse, VariableAdapter

@dataclass
class Loading(Variable):
    # Basic load configuration
    lateral_load_type: int = 0
    dead_load_1: int = 0
    live_load_1: int = 0
    dead_load_2: int = 0
    live_load_2: int = 0
    wind_load_1: int = 0
    wind_load_2: int = 0
    earthquake_load_1: int = 0
    earthquake_load_2: int = 0
    prestress_load: int = 0
    prestress_ratio: float = 0.0
    earth_press_load: int = 0
    
    # Load reduction factors
    ll_red_eq: float = 0.0
    ll_red_wind: float = 0.0
    ll_red_weight: float = 0.0
    ll_red_main: float = 0.0
    
    # Combination settings
    comb_type: int = 0
    comb_option: int = 0
    num_load_system: int = 0
    num_load_case: Tuple[int, int] = (0, 0)
    
    # Variable-length combinations
    combo_factored: Dict[int, List[float]] = field(default_factory=list)
    combo_unfactored: Dict[int, List[float]] = field(default_factory=list)
    
    # Additional load settings
    reduce_temp: int = 0
    use_unity: int = 0
    service_wind_1: int = 0
    service_wind_2: int = 0
    rain_load: int = 0
    temp_worker: int = 0
    comb_uplift: int = 0
    comb_wind: int = 0
    use_vert_eq: int = 0
    uplift_water: int = 0
    
    # Notional loads
    notional_load_1a: int = 0
    notional_load_1b: int = 0
    notional_load_2a: int = 0
    notional_load_2b: int = 0
    use_notional_gravity: int = 0
    use_notional_lateral: int = 0
    notional_coeff: float = 0.0
    
    # Additional load patterns
    qll_1: int = 0
    qll_2: int = 0
    qll_3: int = 0
    axle_moving: int = 0
    displacement: int = 0
    init_stress: int = 0

    key_map: ClassVar[Dict[str, str]] = {
        "lateral_load_type": "Lateral Load Type",
        "dead_load_1": "Dead Load #1",
        "live_load_1": "Live Load #1",
        "dead_load_2": "Dead Load #2",
        "live_load_2": "Live Load #2",
        "wind_load_1": "Wind Load #1",
        "wind_load_2": "Wind Load #2",
        "earthquake_load_1": "Earthquake  Load #1",
        "earthquake_load_2": "Earthquake  Load #2",
        "prestress_load": "Prestressed Load #",
        "prestress_ratio": "Prestressed Pe/Po Ratio",
        "earth_press_load": "Earth Press Load #",
        "ll_red_eq": "LL Reduction for Earthquake",
        "ll_red_wind": "LL Reduction for Wind Load",
        "ll_red_weight": "LL Reduction for Weight/Mass",
        "ll_red_main": "LL Reduction for Main Girder",
        "comb_type": "Load Combination Type",
        "comb_option": "Load Combination Option",
        "num_load_system": "Number of Load System",
        "num_load_case": "Number of Load Case",
        "reduce_temp": "Reduced Load Factor By 30pct for Temporary Load",
        "use_unity": "Use Unity Load Factors",
        "service_wind_1": "Service Wind Load #1",
        "service_wind_2": "Service Wind Load #2",
        "rain_load": "Rain/Storm Load   #",
        "temp_worker": "Temp Worker Load  #",
        "comb_uplift": "Combination for Uplift",
        "comb_wind": "Combination for Wind Load",
        "use_vert_eq": "Use Vertical Earthquake",
        "uplift_water": "Uplift Water Pressure",
        "notional_load_1a": "Notional Load #1",
        "notional_load_1b": "Notional Load #1",
        "notional_load_2a": "Notional Load #2",
        "notional_load_2b": "Notional Load #2",
        "use_notional_gravity": "Use Notional Load for Gravity LoadComb",
        "use_notional_lateral": "Use Notional Load for Lateral LoadComb",
        "notional_coeff": "Notional Load Coeffcient",
        "qll_1": "QLL Load Pattern #1",
        "qll_2": "QLL Load Pattern #2",
        "qll_3": "QLL Load Pattern #3",
        "axle_moving": "Truck/Train Axle Moving Load",
        "displacement": "Displacement Load",
        "init_stress": "Initial Stress Load",
    }


class LoadingParse(VariableParse[Loading]):
    block_key = "LOADING"
    target_cls = Loading

    @classmethod
    def from_mdl(cls, model: Model) -> Loading:
        block = model.blocks.get(cls.block_key)
        if not block:
            raise ValueError(f"Block '{cls.block_key}' not found in model")

        lines = iter(block.body)
        parsed = {}
        combo_factored = {}
        combo_unfactored = {}
        num_factored = 0
        num_unfactored = 0
        parsing_unfactored = False

        key_to_field = {v: k for k, v in cls.target_cls.key_map.items()}

        for line in lines:
            line = line.strip()
            if not line or line.startswith("*") or line == "Unfactored Load Combination":
                if line == "Unfactored Load Combination":
                    parsing_unfactored = True
                continue

            if line.startswith("Number of Load Case"):
                match = re.search(r"=\s*(\d+),\s*(\d+)", line)
                if match:
                    num_factored, num_unfactored = int(match.group(1)), int(match.group(2))
                    parsed["num_load_case"] = (num_factored, num_unfactored)

            elif "Combination #" in line and ("(Factored)" in line or "(Unfactored)" in line):
                match = re.search(r"Combination #\s*(\d+)", line)
                values = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", line) if '.' in x or x.isdigit()]
                if not match or len(values) < 2:
                    continue
                index = int(match.group(1))
                combo_values = values[1:]  # skip combo number

                if "(Factored)" in line:
                    combo_factored[index] = combo_values
                elif "(Unfactored)" in line:
                    combo_unfactored[index] = combo_values

            else:
                match = re.match(r"^(.*?)\s*=\s*(-?[\d.]+)", line)
                if match:
                    key, val = match.groups()
                    key = key.strip().split(":")[0].strip()
                    field = key_to_field.get(key)
                    if field:
                        try:
                            parsed[field] = int(val) if '.' not in val else float(val)
                        except ValueError:
                            parsed[field] = float(val)

        if num_factored > 0:
            parsed["combo_factored"] = {k: combo_factored[k] for k in sorted(combo_factored)[:num_factored]}
        else:
            parsed["combo_factored"] = combo_factored

        if num_unfactored > 0:
            parsed["combo_unfactored"] = {k: combo_unfactored[k] for k in sorted(combo_unfactored)[:num_unfactored]}
        else:
            parsed["combo_unfactored"] = combo_unfactored

        return cls._create_instance(parsed)


    @classmethod
    def _create_instance(cls, parsed_values: Dict[str, Any]) -> Loading:
        """Create Loading instance with proper defaults for missing fields."""
        # Get all field names from the dataclass
        field_names = {f.name for f in fields(cls.target_cls)}
        
        # Create kwargs with defaults for missing fields
        kwargs = {}
        for field_info in fields(cls.target_cls):
            if field_info.name in parsed_values:
                kwargs[field_info.name] = parsed_values[field_info.name]
            elif field_info.default is not field_info.default_factory:
                kwargs[field_info.name] = field_info.default
            elif field_info.default_factory is not field_info.default_factory:
                kwargs[field_info.name] = field_info.default_factory()
            # If no default is specified, the dataclass will handle it

        return cls.target_cls(**kwargs)

class LoadingAdapter(VariableAdapter[Loading]):
    block_key = "LOADING"
    target_cls = Loading

    @classmethod
    def to_string(cls, loading: Loading) -> str:
        lines = [f"*{cls.block_key}*"]
        lines.append(f"  Lateral Load Type = {loading.lateral_load_type}")
        lines.append(f"  Dead Load #1 = {loading.dead_load_1}")
        lines.append(f"  Live Load #1 = {loading.live_load_1}")
        lines.append(f"  Dead Load #2 = {loading.dead_load_2}")
        lines.append(f"  Live Load #2 = {loading.live_load_2}")
        lines.append(f"  Wind Load #1 = {loading.wind_load_1}")
        lines.append(f"  Wind Load #2 = {loading.wind_load_2}")
        lines.append(f"  Earthquake  Load #1 = {loading.earthquake_load_1}")
        lines.append(f"  Earthquake  Load #2 = {loading.earthquake_load_2}")
        lines.append(f"  Prestressed Load # =  {loading.prestress_load} : (Service)")
        lines.append(f"  Prestressed Pe/Po Ratio =  {loading.prestress_ratio:.3f} : (Ratio of Pe/Po)")
        lines.append(f"  Earth Press Load #  = {loading.earth_press_load}")
        lines.append(f"  LL Reduction for Earthquake  =  {loading.ll_red_eq:.3f}")
        lines.append(f"  LL Reduction for Wind Load   =  {loading.ll_red_wind:.3f}")
        lines.append(f"  LL Reduction for Weight/Mass =  {loading.ll_red_weight:.3f}")
        lines.append(f"  LL Reduction for Main Girder =  {loading.ll_red_main:.3f}")
        lines.append(f"  Load Combination Type   = {loading.comb_type}")
        lines.append(f"  Load Combination Option = {loading.comb_option}")
        lines.append(f"  Number of Load System   = {loading.num_load_system}")
        lines.append(f"  Number of Load Case     = {loading.num_load_case[0]}, {loading.num_load_case[1]}")
        for i in sorted(loading.combo_factored):
            row = loading.combo_factored[i]
            lines.append(f"  Combination # {i} (Factored) =  " + " ".join(f"{v:7.3f}" for v in row))
        lines.append(f"  Reduced Load Factor By 30pct for Temporary Load = {loading.reduce_temp}")
        lines.append(f"  Use Unity Load Factors = {loading.use_unity}")
        lines.append(f"  Service Wind Load #1 = {loading.service_wind_1}")
        lines.append(f"  Service Wind Load #2 = {loading.service_wind_2}")
        lines.append(f"  Rain/Storm Load   #  = {loading.rain_load}")
        lines.append(f"  Temp Worker Load  #  = {loading.temp_worker}")
        lines.append(f"  Combination for Uplift    = {loading.comb_uplift}")
        lines.append(f"  Combination for Wind Load = {loading.comb_wind}")
        lines.append(f"  Use Vertical Earthquake   = {loading.use_vert_eq}")
        lines.append(f"  Uplift Water Pressure = {loading.uplift_water}")
        lines.append(f"  Notional Load #1      = {loading.notional_load_1a}")
        lines.append(f"  Notional Load #1      = {loading.notional_load_1b}")
        lines.append(f"  Notional Load #2      = {loading.notional_load_2a}")
        lines.append(f"  Notional Load #2      = {loading.notional_load_2b}")
        lines.append(f"  Use Notional Load for Gravity LoadComb = {loading.use_notional_gravity}")
        lines.append(f"  Use Notional Load for Lateral LoadComb = {loading.use_notional_lateral}")
        lines.append(f"  Notional Load Coeffcient               = {loading.notional_coeff:.6f}")
        lines.append(f"  QLL Load Pattern #1   = {loading.qll_1}")
        lines.append(f"  QLL Load Pattern #2   = {loading.qll_2}")
        lines.append(f"  QLL Load Pattern #3   = {loading.qll_3}")
        lines.append(f"  Truck/Train Axle Moving Load = {loading.axle_moving}")
        lines.append(f"  Displacement Load     = {loading.displacement}")
        lines.append(f"  Initial Stress Load   = {loading.init_stress}")
        lines.append("Unfactored Load Combination")
        for i in sorted(loading.combo_unfactored):
            row = loading.combo_unfactored[i]
            lines.append(f"  Combination # {i} (Unfactored) =  " + " ".join(f"{v:7.3f}" for v in row))
        return "\n".join(lines)
    
    @classmethod
    def to_block(cls, loading: Loading) -> Block:
        lines = cls.to_string(loading).splitlines()[1:]
        return BlockAdapter.from_lines(header=cls.block_key, lines=lines)

    @classmethod
    def to_model(cls, loading: Loading, model: Model) -> Model:
        block = cls.to_block(loading)
        model.blocks[cls.block_key] = block
        return model

class LoadingEngine:
    """Builder class to easily construct Loading instances with predefined configurations."""
    
    def __init__(self):
        self.loading = Loading()
    
    def with_basic_loads(self, 
                        lateral_type: int = 4,
                        dead_1: int = 1, live_1: int = 2,
                        dead_2: int = 1, live_2: int = 2,
                        wind_1: int = 5, wind_2: int = 6,
                        eq_1: int = 3, eq_2: int = 4) -> 'LoadingEngine':
        """Set basic load type assignments."""
        self.loading.lateral_load_type = lateral_type
        self.loading.dead_load_1 = dead_1
        self.loading.live_load_1 = live_1
        self.loading.dead_load_2 = dead_2
        self.loading.live_load_2 = live_2
        self.loading.wind_load_1 = wind_1
        self.loading.wind_load_2 = wind_2
        self.loading.earthquake_load_1 = eq_1
        self.loading.earthquake_load_2 = eq_2
        return self
    
    def with_prestress(self, load_num: int = 0, ratio: float = 0.700) -> 'LoadingEngine':
        """Set prestress load configuration."""
        self.loading.prestress_load = load_num
        self.loading.prestress_ratio = ratio
        return self
    
    def with_load_reductions(self, 
                            eq: float = 0.500,
                            wind: float = 1.000,
                            weight: float = 0.250,
                            main: float = 1.000) -> 'LoadingEngine':
        """Set live load reduction factors."""
        self.loading.ll_red_eq = eq
        self.loading.ll_red_wind = wind
        self.loading.ll_red_weight = weight
        self.loading.ll_red_main = main
        return self
    
    def with_combination_settings(self, 
                                 comb_type: int = 0,
                                 comb_option: int = 2,
                                 num_system: int = 7,
                                 num_factored: int = 6,
                                 num_unfactored: int = 6) -> 'LoadingEngine':
        """Set load combination configuration."""
        self.loading.comb_type = comb_type
        self.loading.comb_option = comb_option
        self.loading.num_load_system = num_system
        self.loading.num_load_case = (num_factored, num_unfactored)
        return self
    
    def with_identity_factored_combinations(self, num_loads: int = 7) -> 'LoadingEngine':
        """Create identity matrix for factored combinations (1.0 on diagonal, 0.0 elsewhere)."""
        combinations = {}
        for i in range(num_loads):
            row = [0.000] * num_loads
            row[i] = 1.000
            combinations[i + 1] = row
        self.loading.combo_factored = combinations
        return self
    
    def with_custom_factored_combinations(self, combinations: List[List[float]]) -> 'LoadingEngine':
        """Set custom factored combinations."""
        self.loading.combo_factored = {i + 1: row for i, row in enumerate(combinations)}
        return self
    
    def with_unfactored_combinations(self, num_loads: int = 7) -> 'LoadingEngine':
        """Set unfactored combinations with first combination and zeros for the rest."""
        combinations = {}
        for i in range(num_loads):
            row = [0.000] * num_loads
            row[i] = 1.000
            combinations[i + 1] = row
        self.loading.combo_unfactored = combinations
        return self
    
    def with_service_settings(self, 
                             uplift_comb: int = 1,
                             wind_comb: int = 1,
                             use_vert_eq: int = 1) -> 'LoadingEngine':
        """Set service load settings."""
        self.loading.comb_uplift = uplift_comb
        self.loading.comb_wind = wind_comb
        self.loading.use_vert_eq = use_vert_eq
        return self
    
    def with_notional_loads(self, coeff: float = 0.002000) -> 'LoadingEngine':
        """Set notional load coefficient."""
        self.loading.notional_coeff = coeff
        return self
    
    def set_load_combination(self) -> Loading:
        """Build the exact Loading instance from your example."""
        return (self
                .with_basic_loads()
                .with_prestress()
                .with_load_reductions()
                .with_combination_settings()
                .with_identity_factored_combinations()
                .with_unfactored_combinations()
                .with_service_settings()
                .with_notional_loads()
                .build())
    
    def build(self) -> Loading:
        """Build and return the Loading instance."""
        return self.loading
