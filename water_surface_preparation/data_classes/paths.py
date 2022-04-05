from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PathsForOneProcess:
    path_to_shoreline: str
    paths_to_centerlines: list[str]
    path_to_raster: str
    path_to_additional_points: Optional[str]
    path_to_gps_points: Optional[str]
