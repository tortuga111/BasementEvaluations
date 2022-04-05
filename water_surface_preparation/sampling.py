import geopandas as gpd
import numpy as np
from shapely.geometry import MultiPoint, LineString
from shapely.ops import substring


def sample_points_along_line(open_shore_shoreline: gpd.GeoDataFrame, sampling_distance: float) -> gpd.GeoDataFrame:
    multi_point = MultiPoint()
    for line in (geom for geom in open_shore_shoreline.geometry if isinstance(geom, LineString)):
        if np.isnan(line.length):
            continue
        for i in np.arange(0, line.length, sampling_distance):
            s = substring(line, i, i + sampling_distance)
            multi_point = multi_point.union(s.boundary)
    return gpd.GeoDataFrame(
        geometry=(gpd.GeoSeries(point_series for point_series in multi_point)), crs=open_shore_shoreline.crs
    )
