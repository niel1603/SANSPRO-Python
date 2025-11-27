from dataclasses import dataclass, field


from object._object_abstract import Object

@dataclass
class Story(Object):
    name: str
    column_layout: int
    beam_layout: int
    shearwall_layout: int
    rigid: bool
    force_opt: int
    height: float
    live_lrf: float
    col_axial_lrf: float
    plate_thick: float
    misc1: str = field(repr=False)
    misc2: int = field(repr=False)