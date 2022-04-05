import geopandas as gpd
import rasterio as rio
from rasterio import DatasetReader
from tqdm import tqdm


def extract_elevation_from_raster(points_to_intersect: gpd.GeoDataFrame, path_to_raster: str) -> gpd.GeoDataFrame:
    with rio.open(path_to_raster) as raster_to_intersect:
        raster_to_intersect: DatasetReader
        points_to_intersect["z_raster"] = 0.0
        temp_raster = raster_to_intersect.read(1)

        for ID, row in tqdm(points_to_intersect.iterrows()):
            longitude = row["geometry"].x
            latitude = row["geometry"].y
            row_index, col_index = raster_to_intersect.index(longitude, latitude)
            points_to_intersect.loc[ID, "z_raster"] = temp_raster[row_index, col_index]

    return points_to_intersect
