from typing import ClassVar, Dict
from dataclasses import dataclass

from variable._variable_abstract import (
    Variable, 
    VariableParse, 
    VariableAdapter
    )

@dataclass
class Screen(Variable):
    snap_to_grid: int
    snap_ratio: int
    auto_working_range: int

    building_floor_xmin: float
    building_floor_xmax: float
    building_floor_ymin: float
    building_floor_ymax: float

    grid_spacing_dx: float
    grid_spacing_dy: float

    autoscale_flag: int
    drawing_scale: float
    zoom_factor: float
    displacement_scale: float
    rotation_scale: float

    drawing_scale_column: float
    drawing_scale_wall: float
    drawing_scale_beam: float
    drawing_scale_surface_load: float
    drawing_scale_distributed_force: float
    drawing_scale_distributed_torsion: float
    drawing_scale_point_force: float
    drawing_scale_point_moment: float
    drawing_scale_point_torsion: float

    building_floor_x_margin: float
    building_floor_y_margin: float
    building_floor_x_axis: float
    building_floor_y_axis: float

    snap_to_axis: int
    dark_background: int
    draw_axis_lines: int
    show_node: int
    show_cline: int
    show_slab: int
    ortho_flag: int
    perspective_flag: int
    perspective_factor: float
    render_type: int
    show_ray_lines: int
    show_equivload_x: int
    show_equivload_z: int

    key_map: ClassVar[Dict[str, str]] = {
        "snap_to_grid": "Snap to Grid",
        "snap_ratio": "Snap Ratio",
        "auto_working_range": "Auto Working Range",

        "building_floor_xmin": "Building Floor Xmin",
        "building_floor_xmax": "Building Floor Xmax",
        "building_floor_ymin": "Building Floor Ymin",
        "building_floor_ymax": "Building Floor Ymax",

        "grid_spacing_dx": "Grid Spacing,  DX",
        "grid_spacing_dy": "Grid Spacing,  DY",

        "autoscale_flag": "AutoScale Flag",
        "drawing_scale": "Drawing  Scale",
        "zoom_factor": "Zoom Factor",
        "displacement_scale": "Displacement Scale",
        "rotation_scale": "Rotation Scale",

        "drawing_scale_column": "Drawing Scale, Column",
        "drawing_scale_wall": "Drawing Scale, Wall",
        "drawing_scale_beam": "Drawing Scale, Beam",
        "drawing_scale_surface_load": "Drawing Scale, Surface Load",
        "drawing_scale_distributed_force": "Drawing Scale, Distributed Force",
        "drawing_scale_distributed_torsion": "Drawing Scale, Distributed Torsion",
        "drawing_scale_point_force": "Drawing Scale, Point   Force",
        "drawing_scale_point_moment": "Drawing Scale, Point   Moment",
        "drawing_scale_point_torsion": "Drawing Scale, Point   Torsion",

        "building_floor_x_margin": "Building Floor, X Margin",
        "building_floor_y_margin": "Building Floor, Y Margin",
        "building_floor_x_axis": "Building Floor, X Axis",
        "building_floor_y_axis": "Building Floor, Y Axis",

        "snap_to_axis": "Snap to Axis",
        "dark_background": "Dark Background",
        "draw_axis_lines": "Draw Axis Lines",
        "show_node": "Show Node",
        "show_cline": "Show CLine",
        "show_slab": "Show Slab",
        "ortho_flag": "Ortho Flag",
        "perspective_flag": "Perspective Flag",
        "perspective_factor": "Perspective Factor",
        "render_type": "Render Type",
        "show_ray_lines": "Show Ray Lines",
        "show_equivload_x": "Show EquivLoad, X",
        "show_equivload_z": "Show EquivLoad, Z",
    }


class ScreenParse(VariableParse[Screen]):
    block_key = "SCREEN"
    target_cls = Screen


class ScreenAdapter(VariableAdapter[Screen]):

    @staticmethod
    def format_line(label: str, value) -> str:
        return f"  {label:<28}= {value}"

    block_key = "SCREEN"
    target_cls = Screen
