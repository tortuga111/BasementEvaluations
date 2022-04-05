import os

import geopandas as gpd
import rasterio as rio
from rasterio import DatasetReader

# Read file using gpd.read_file()
from tqdm import tqdm


def get_data_path() -> str:
    return os.path.join(os.getcwd(), "data")


def extract_elevation_from_raster(path_to_points: str, path_raster: str) -> gpd.GeoDataFrame:
    points_to_intersect = gpd.read_file(path_to_points)
    with rio.open(path_raster) as raster_to_intersect:
        raster_to_intersect: DatasetReader
        points_to_intersect["z_raster"] = 0.0
        temp_raster = raster_to_intersect.read(1)

        for ID, row in tqdm(points_to_intersect.iterrows()):
            longitude = row["geometry"].x
            latitude = row["geometry"].y
            row_index, col_index = raster_to_intersect.index(longitude, latitude)
            points_to_intersect.loc[ID, "z_raster"] = temp_raster[row_index, col_index]

    return points_to_intersect


def save_file_as_shp(path_to_points, path_to_raster, path_to_results):
    points_with_raster_values = extract_elevation_from_raster(path_to_points, path_to_raster)
    points_with_raster_values.to_file(os.path.join(path_to_results, "points_with_raster_values.shp"))


def main() -> None:
    path_to_points: str = "/02_prep_bathy/00_gcp_prep/01_dsm_comparison_gpselev_BF2020/comparison_gps_dsm_BF2020.shp"

    path_to_raster: str = "/01_prep_raster/BF_2020_dsm_AOIextended.tif"

    path_to_results: str = os.path.join(os.getcwd(), "/02_prep_bathy/00_gcp_prep")

    save_file_as_shp(path_to_points, path_to_raster, path_to_results)


if __name__ == "__main__":
    main()
