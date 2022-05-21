import wget
import rasterio as rio
from rasterio import mask

import matplotlib.pyplot as plt

import numpy as np
import geopandas as gpd
import pandas as pd

import folium


from utils.loading import load_data_with_crs_2056


def load_raster(path_to_raster):
    with rio.open(path_to_raster) as raster_to_process:
        raster_to_process: DatasetReader
    return raster_to_process


def main():
    path_to_raster = r"C:\Users\nflue\Documents\Masterarbeit\02_Data\03_Bathymetry\DoDs\dod_v2\dod_af20_min_bf20.tif"

    path_to_polygon = r"C:\Users\nflue\Desktop\experiments\experiments_old_mesh_batch1\runs_with_kst30_and_40_and_grain0.05_and_0.082_results\polygons\elevation_change_discharge_file@Hydrograph_HW2020_115000.txt$end@115000$fixed_bed@0$grain_diameter@0.05$kst_regions@30.shp"

    polygon_as_area_of_interest = load_data_with_crs_2056(path_to_polygon)
    dod = load_raster(path_to_raster)

    _results = []
    for i in polygon_as_area_of_interest["geometry"]:
        roi = polygon_as_area_of_interest[polygon_as_area_of_interest.geometry == i]

        # using the mask.mask module from Rasterio to specify the ROI
        gtraster, bound = mask.mask(dod, roi["geometry"], crop=True)

        # values greater than 0 represent the estimated population count for that pixel
        _results.append(gtraster[0][gtraster[0] >= 0].mean())

        # Save the estimated counts for each year in a new column
    polygon_as_area_of_interest["dz_dod"] = _results


if __name__ == "__main__":
    main()
