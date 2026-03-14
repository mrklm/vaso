from dataclasses import dataclass, field
from typing import List


@dataclass
class Profile:
    z_ratio: float
    diameter: float
    sides: int
    rotation_deg: float
    scale_x: float = 1.0
    scale_y: float = 1.0
    offset_x: float = 0.0
    offset_y: float = 0.0


@dataclass
class VaseParameters:
    height_mm: float = 180.0
    wall_thickness_mm: float = 2.4
    bottom_thickness_mm: float = 3.0

    radial_samples: int = 96
    vertical_samples: int = 120

    open_top: bool = True
    close_bottom: bool = True

    profiles: List[Profile] = field(default_factory=list)