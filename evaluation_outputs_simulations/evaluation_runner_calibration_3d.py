import geopandas as gpd
import pandas as pd
from tqdm import tqdm

from evaluation_outputs_simulations.evaluation_runner_calibration_profiles import load_data_from_simulations, \
    create_summarising_mesh_with_all_results
from utils.loading import load_data_with_crs_2056


def main():
    bottom_elevation, flow_velocity, hydraulic_state = load_data_from_simulations()
    path_to_polygon_as_area_of_interest = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af_1.shp"
    path_to_dod_as_polygon = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\DoDs\\AF20_min_BF20_reclass_as_polygon.shp"

    mesh_with_all_results = create_summarising_mesh_with_all_results(bottom_elevation, flow_velocity, hydraulic_state)

    masking_polygons_for_evaluation = load_data_with_crs_2056(path_to_polygon_as_area_of_interest)
    dod_as_polygon = load_data_with_crs_2056(path_to_dod_as_polygon)

    empty_list_for_clipped_dod = []
    for polygon_index, polygon in tqdm(enumerate(masking_polygons_for_evaluation.geometry)):
        empty_list_for_clipped_dod.append(gpd.clip(dod_as_polygon, mask=polygon, keep_geom_type=False))
    clipped_dod = gpd.GeoDataFrame(
        pd.concat(empty_list_for_clipped_dod, ignore_index=True), crs=dod_as_polygon.crs
    )

    clipped_dod["dz_dod"] = None
    clipped_dod.loc[clipped_dod["gridcode"] == 1, "dz_dod"] = "deposition"

    clipped_dod.loc[clipped_dod["gridcode"] == -1, "dz_dod"] = "erosion"

    clipped_dod.loc[clipped_dod["gridcode"] == 0, "dz_dod"] = "stable"


    empty_list_for_clipped_polygons = []
    for polygon_index, polygon in tqdm(enumerate(masking_polygons_for_evaluation.geometry)):
        empty_list_for_clipped_polygons.append(gpd.clip(mesh_with_all_results, mask=polygon, keep_geom_type=False))
    clipped_mesh = gpd.GeoDataFrame(
        pd.concat(empty_list_for_clipped_polygons, ignore_index=True), crs=masking_polygons_for_evaluation.crs
    )

    clipped_mesh["dz_sim"] = None
    clipped_mesh.loc[clipped_mesh["delta_z"] > 0.01, "dz_sim"] = "deposition"

    clipped_mesh.loc[clipped_mesh["delta_z"] < -0.01, "dz_sim"] = "erosion"

    condition = (clipped_mesh["delta_z"] >= -0.1) & (clipped_mesh["delta_z"] <= 0.1)
    clipped_mesh.loc[condition, "dz_sim"] = "stable"
    clipped_mesh.to_file("clipped_mesh.shp")

    union_of_dod_and_mesh = gpd.overlay(clipped_mesh, clipped_dod, how='union')

    dz_dod = union_of_dod_and_mesh["dz_dod"]
    dz_sim = union_of_dod_and_mesh["dz_sim"]
    union_of_dod_and_mesh["dod_vs_sim"] = f"{dz_dod} (dz_dod) vs {dz_sim} (dz_sim)"

    union_of_dod_and_mesh["comparison"] = None
    union_of_dod_and_mesh.loc[union_of_dod_and_mesh["dz_dod"] == union_of_dod_and_mesh["dz_sim"], "comparison"] = "identical"

    union_of_dod_and_mesh.loc[
        union_of_dod_and_mesh["dz_dod"] != union_of_dod_and_mesh["dz_sim"], "comparison"] = "different"

    union_of_dod_and_mesh.to_file("out\\union_of_dod_and_mesh.shp")



if __name__ == "__main__":
    main()
