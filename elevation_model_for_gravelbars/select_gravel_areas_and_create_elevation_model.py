from dataclasses import dataclass
from enum import Enum

import matplotlib.pyplot as plt
import rasterio as rio
import rasterio.features
from geopandas import GeoDataFrame
from osgeo import gdal
from rasterio import DatasetReader

from utils.loading import load_data_with_crs_2056


# load data: polygon with gravel areas, raster files dsm and dtm


@dataclass(frozen=True)
class PathsForOneProcess:
    path_to_polygons_gravel: str
    path_to_dsm: str
    path_to_dtm: str
    pass


class HabitatTypes(Enum):
    water_surface = 0
    gravel = 1
    vegetation = 2


class Scenario(Enum):
    af_2021 = "AF_2021"
    af_2020 = "AF_2020"
    bf_2020 = "BF_2020"


def get_all_paths_for_one_scenario(demanded_scenario: Scenario) -> PathsForOneProcess:
    if demanded_scenario == Scenario.af_2021:
        return PathsForOneProcess(
            path_to_polygons_gravel=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01_AF2021_wettedarea\\AF2021_gravel\\shoreline_with_gravel_AF2021_polygon.shp"
            ),
            path_to_dsm=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\" "01_prep_raster\\AF_2021_dsm_AOIextended.tif"
            ),
            path_to_dtm=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\01_prep_raster\\AF_2021_dtm_AOIextended.tif"
            ),
        )

    if demanded_scenario == Scenario.af_2020:
        return PathsForOneProcess(
            path_to_polygons_gravel=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_gravel\\shoreline_with_gravel_AF2020_polygon_03.shp"
            ),
            path_to_dsm=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\01_prep_raster\\AF_2020_dsm_AOIextended_minus020.tif"
            ),
            path_to_dtm=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\01_prep_raster\\AF_2020_dtm_AOIextended_minus020.tif"
            ),
        )

    if demanded_scenario == Scenario.bf_2020:
        return PathsForOneProcess(
            path_to_polygons_gravel=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_gravel\\BF2020_shoreline_with_gravel_polygon.shp"
            ),
            path_to_dsm=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\01_prep_raster\\BF_2020_dsm_AOIextended.tif"
            ),
            path_to_dtm=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\01_prep_raster\\BF_2020_dtm_AOIextended.tif"
            ),
        )

    else:
        raise NotImplementedError(f"{Scenario} is not implemented yet")


def main():
    # select gravel areas in polygon file (value = 1) and create a separate layer
    # crop .tifs by gravel area
    # resample .tifs to 0.5
    # dsm - dtm to eliminate vegetation
    # create gravel mask: set values not 0 to 0, and 0 values to 1
    # multiply mask with dsm
    # raster to points: output point .shp file.

    scenario = Scenario.bf_2020
    paths = get_all_paths_for_one_scenario(scenario)
    all_habitat_polygons = load_data_with_crs_2056(paths.path_to_polygons_gravel)

    gravel_bars_polygons: GeoDataFrame = all_habitat_polygons[
        all_habitat_polygons["habitat"] == HabitatTypes.gravel.value
    ]
    gravel_bars_polygons.to_file(f"..\\output_gravel_bars\\gravel_bars_polygon_layer_{scenario.value}.shp")
    # dsm = load_raster(paths.path_to_dsm)
    dsm = paths.path_to_dsm
    dtm = paths.path_to_dtm

    dsm_resampled = resample_raster(dsm, f"dsm_{scenario.value}_resample_to_05")
    dtm_resampled = resample_raster(dtm, f"dtm_{scenario.value}_resample_to_05")


def load_raster(path_to_raster):
    with rio.open(path_to_raster) as raster_to_process:
        raster_to_process: DatasetReader
    return raster_to_process


def resample_raster(raster, name_clipped_raster) -> str:
    name_raster_clip = raster
    output_directory_and_file_name = f"..\\output_gravel_bars\\{name_clipped_raster}.tif"
    options = gdal.WarpOptions(
        options=["tr"],
        xRes=0.5,
        yRes=0.5,
        resampleAlg="bilinear",
        format="GTiff",
    )
    resampled_raster = gdal.Warp(output_directory_and_file_name, name_raster_clip, options=options)
    return output_directory_and_file_name


if __name__ == "__main__":
    main()
