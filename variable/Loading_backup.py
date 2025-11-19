import re
from typing import ClassVar, Dict, List, Union, Tuple, Any
from dataclasses import dataclass, fields, field
from SANSPRO.model.Model import Block, Model, BlockAdapter
from SANSPRO.variable.VariableAbstract import Variable, VariableParse, VariableAdapter

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
    combo_factored: List[List[float]] = field(default_factory=list)
    combo_unfactored: List[List[float]] = field(default_factory=list)
    
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
        combo_factored = []
        combo_unfactored = []
        num_factored = 0
        num_unfactored = 0
        parsing_unfactored = False

        # Create reverse mapping for efficient lookup
        key_to_field = {v: k for k, v in cls.target_cls.key_map.items()}

        for line in lines:
            line = line.strip()
            
            # Skip empty lines and headers
            if not line or line.startswith("*") or line == "Unfactored Load Combination":
                if line == "Unfactored Load Combination":
                    parsing_unfactored = True
                continue

            # Parse number of load cases
            if line.startswith("Number of Load Case"):
                match = re.search(r"=\s*(\d+),\s*(\d+)", line)
                if match:
                    num_factored, num_unfactored = int(match.group(1)), int(match.group(2))
                    parsed["num_load_case"] = (num_factored, num_unfactored)

            # Parse combination lines
            elif "Combination #" in line and ("(Factored)" in line or "(Unfactored)" in line):
                # Extract all numeric values from the line
                values = [float(x) for x in re.findall(r"[-+]?\d*\.?\d+", line) if '.' in x or x.isdigit()]
                
                if "(Factored)" in line:
                    combo_factored.append(values[1:])  # Skip combination number
                elif "(Unfactored)" in line:
                    combo_unfactored.append(values[1:])  # Skip combination number

            # Parse regular key-value pairs
            else:
                match = re.match(r"^(.*?)\s*=\s*(-?[\d.]+)", line)
                if match:
                    key, val = match.groups()
                    # Clean key by removing comments and extra spaces
                    key = key.strip().split(":")[0].strip()
                    
                    # Find matching field
                    field = key_to_field.get(key)
                    if field:
                        try:
                            # Try integer first, then float
                            parsed[field] = int(val) if '.' not in val else float(val)
                        except ValueError:
                            parsed[field] = float(val)

        # Store combinations (trim to actual counts if specified)
        if num_factored > 0:
            parsed["combo_factored"] = combo_factored[:num_factored]
        else:
            parsed["combo_factored"] = combo_factored

        if num_unfactored > 0:
            parsed["combo_unfactored"] = combo_unfactored[:num_unfactored]
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

    @staticmethod
    def format_line(label: str, value: Union[int, float, str]) -> str:
        """Format a simple key-value line."""
        return f"  {label:<32}= {value}"

    @classmethod
    def _format_content(cls, instance: Loading) -> List[str]:
        """Format the complete content including combinations."""
        lines = []
        
        # Format regular key-value pairs
        for field, label in cls.target_cls.key_map.items():
            val = getattr(instance, field)
            
            # Handle special formatting for tuples
            if isinstance(val, tuple) and field == "num_load_case":
                formatted_value = f"{val[0]}, {val[1]}"
            else:
                formatted_value = val
                
            lines.append(cls.format_line(label, formatted_value))

        # Add factored combinations
        for i, row in enumerate(instance.combo_factored, 1):
            combination_line = f"  Combination # {i:<2} (Factored)   = " + "   ".join(f"{v:7.3f}" for v in row)
            lines.append(combination_line)

        # Add unfactored combinations section
        if instance.combo_unfactored:
            lines.append("Unfactored Load Combination")
            for i, row in enumerate(instance.combo_unfactored, 1):
                combination_line = f"  Combination # {i:<2} (Unfactored) = " + "   ".join(f"{v:7.3f}" for v in row)
                lines.append(combination_line)

        return lines

    @classmethod
    def to_block(cls, instance: Loading) -> Block:
        """Convert Loading instance to Block."""
        lines = [f"*{cls.block_key}*"]
        lines.extend(cls._format_content(instance))
        return BlockAdapter.from_lines(header=cls.block_key, lines=lines)


    @classmethod
    def to_model(cls, instance: Loading, model: Model) -> Model:
        """Add Loading instance as block to model and return the updated model."""
        # Create the block with properly formatted content
        block_lines = []
        
        # Add the header
        block_lines.append(f"*{cls.block_key}*")
        
        # Format regular key-value pairs (excluding combinations)
        for field, label in cls.target_cls.key_map.items():
            val = getattr(instance, field)
            
            # Handle special formatting for tuples
            if isinstance(val, tuple) and field == "num_load_case":
                formatted_value = f"{val[0]}, {val[1]}"
            elif isinstance(val, float):
                # Format floats with appropriate precision
                if field == "prestress_ratio" or field == "notional_coeff":
                    formatted_value = f"{val:.6f}"
                else:
                    formatted_value = f"{val:.3f}"
            else:
                formatted_value = str(val)
                
            block_lines.append(cls.format_line(label, formatted_value))

        # Add factored combinations with proper formatting
        for i, row in enumerate(instance.combo_factored, 1):
            combination_line = f"  Combination # {i:<2} (Factored)   = " + "   ".join(f"{v:7.3f}" for v in row)
            block_lines.append(combination_line)

        # Add unfactored combinations section with proper formatting
        if instance.combo_unfactored:
            block_lines.append("Unfactored Load Combination")
            for i, row in enumerate(instance.combo_unfactored, 1):
                combination_line = f"  Combination # {i:>2} (Unfactored) = " + "   ".join(f"{v:7.3f}" for v in row)
                block_lines.append(combination_line)

        # Create block using BlockAdapter
        block = BlockAdapter.from_lines(header=cls.block_key, lines=block_lines)
        
        # Add block to model
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
        combinations = []
        for i in range(num_loads):
            row = [0.000] * num_loads
            row[i] = 1.000
            combinations.append(row)
        self.loading.combo_factored = combinations
        return self
    
    def with_custom_factored_combinations(self, combinations: List[List[float]]) -> 'LoadingEngine':
        """Set custom factored combinations."""
        self.loading.combo_factored = combinations
        return self
    
    def with_unfactored_combinations(self, num_loads: int = 7) -> 'LoadingEngine':
        """Set unfactored combinations with first combination and zeros for the rest."""
        combinations = []
        for i in range(num_loads):
            row = [0.000] * num_loads
            row[i] = 1.000
            combinations.append(row)
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
