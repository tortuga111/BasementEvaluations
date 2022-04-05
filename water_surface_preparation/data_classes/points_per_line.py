from dataclasses import dataclass

import geopandas as gpd
from shapely.geometry import Point, LineString


@dataclass
class PointsPerCenterline:
    points: gpd.GeoDataFrame
    center_line: gpd.GeoDataFrame

    def __post_init__(self):
        assert len(self.center_line.geometry) == 1


@dataclass
class ProjectedPointsPerCenterLine:
    projected_points: gpd.GeoDataFrame
    center_line: gpd.GeoDataFrame


class OrderedProjectedPointsPerCenterLine(ProjectedPointsPerCenterLine):
    pass


class ProcessedPointsPerCenterLine(ProjectedPointsPerCenterLine):
    pass


@dataclass(frozen=True)
class TransectLinesAtPoint:
    point: Point
    right_line: LineString
    left_line: LineString
    transect_number: int
    elevation: float
