import geopandas as gpd
import numpy as np
import pandas as pd
from tqdm import tqdm

from utils.loading import load_data_with_crs_2056


def create_union_of_dod_and_simulated_dz_mesh(
    path_to_dod_as_polygon: str,
    mesh_with_all_results: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    dod_as_polygon = load_data_with_crs_2056(path_to_dod_as_polygon)

    mesh_with_all_results["dz_sim"] = None
    mesh_with_all_results.loc[mesh_with_all_results["delta_z"] > 0.01, "dz_sim"] = "deposition"

    mesh_with_all_results.loc[mesh_with_all_results["delta_z"] < -0.01, "dz_sim"] = "erosion"

    condition = (mesh_with_all_results["delta_z"] >= -0.1) & (mesh_with_all_results["delta_z"] <= 0.1)
    mesh_with_all_results.loc[condition, "dz_sim"] = "stable"

    dod_as_polygon["dz_dod"] = None
    dod_as_polygon.loc[dod_as_polygon["gridcode"] == 1, "dz_dod"] = "deposition"

    dod_as_polygon.loc[dod_as_polygon["gridcode"] == -1, "dz_dod"] = "erosion"

    dod_as_polygon.loc[dod_as_polygon["gridcode"] == 0, "dz_dod"] = "stable"

    union_of_dod_and_simulated_dz_mesh = gpd.overlay(
        dod_as_polygon,
        mesh_with_all_results,
        how="union",
        keep_geom_type=True,
    )
    union_of_dod_and_simulated_dz_mesh = union_of_dod_and_simulated_dz_mesh.explode(index_parts=True)

    dz_dod = union_of_dod_and_simulated_dz_mesh["dz_dod"]
    dz_sim = union_of_dod_and_simulated_dz_mesh["dz_sim"]
    union_of_dod_and_simulated_dz_mesh["dod_vs_sim"] = dz_dod + "(dz dod) vs " + dz_sim + "(dz sim)"

    union_of_dod_and_simulated_dz_mesh["comparison"] = None
    union_of_dod_and_simulated_dz_mesh.loc[
        union_of_dod_and_simulated_dz_mesh["dz_dod"] == union_of_dod_and_simulated_dz_mesh["dz_sim"], "comparison"
    ] = "identical"

    union_of_dod_and_simulated_dz_mesh.loc[
        union_of_dod_and_simulated_dz_mesh["dz_dod"] != union_of_dod_and_simulated_dz_mesh["dz_sim"], "comparison"
    ] = "different"

    return union_of_dod_and_simulated_dz_mesh


def clip_mesh_with_polygons(
    mesh_with_all_results: gpd.GeoDataFrame, masking_polygon: gpd.GeoDataFrame, experiment_id: str
) -> gpd.GeoDataFrame:
    empty_list_for_clipped_mesh_elements = []
    for polygon_index, polygon in tqdm(enumerate(masking_polygon.geometry)):
        empty_list_for_clipped_mesh_elements.append(gpd.clip(mesh_with_all_results, mask=polygon, keep_geom_type=True))
    clipped_simulated_deltaz_mesh = gpd.GeoDataFrame(
        pd.concat(empty_list_for_clipped_mesh_elements, ignore_index=True), crs=masking_polygon.crs
    )
    clipped_simulated_deltaz_mesh.to_file(f"out\\polygons\\elevation_change_{experiment_id}.shp")
    return clipped_simulated_deltaz_mesh


def calculate_ratio_of_eroded_area_dod(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    return np.divide(
        sum(
            (union_of_dod_and_simulated_dz_mesh.loc[union_of_dod_and_simulated_dz_mesh["dz_dod"] == "erosion", :])
            .copy(deep=True)
            .area
        ),
        sum(union_of_dod_and_simulated_dz_mesh.area),
    )


def calculate_ratio_of_deposited_area_dod(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    return np.divide(
        sum(
            (union_of_dod_and_simulated_dz_mesh.loc[union_of_dod_and_simulated_dz_mesh["dz_dod"] == "deposition", :])
            .copy(deep=True)
            .area
        ),
        sum(union_of_dod_and_simulated_dz_mesh.area),
    )


def calculate_ratio_of_eroded_area_sim(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    return np.divide(
        sum(
            (union_of_dod_and_simulated_dz_mesh.loc[union_of_dod_and_simulated_dz_mesh["dz_sim"] == "erosion", :])
            .copy(deep=True)
            .area
        ),
        sum(union_of_dod_and_simulated_dz_mesh.area),
    )


def calculate_ratio_of_deposited_area_sim(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    return np.divide(
        sum(
            (union_of_dod_and_simulated_dz_mesh.loc[union_of_dod_and_simulated_dz_mesh["dz_sim"] == "deposition", :])
            .copy(deep=True)
            .area
        ),
        sum(union_of_dod_and_simulated_dz_mesh.area),
    )


def calculate_ratio_of_identical_change(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    return np.divide(
        sum(
            (union_of_dod_and_simulated_dz_mesh.loc[union_of_dod_and_simulated_dz_mesh["comparison"] == "identical", :])
            .copy(deep=True)
            .area
        ),
        sum(union_of_dod_and_simulated_dz_mesh.area),
    )


def calculate_ratio_of_different_change(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    return np.divide(
        sum(
            (union_of_dod_and_simulated_dz_mesh.loc[union_of_dod_and_simulated_dz_mesh["comparison"] == "different", :])
            .copy(deep=True)
            .area
        ),
        sum(union_of_dod_and_simulated_dz_mesh.area),
    )


def calculate_eroded_volume(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame) -> float:
    selection_of_erosion_area = union_of_dod_and_simulated_dz_mesh.loc[lambda x: x["dz_sim"] == "erosion", :]
    return sum(selection_of_erosion_area["volume"])


def calculate_deposited_volume(union_of_dod_and_simulated_dz_mesh: gpd.GeoDataFrame):
    selection_of_deposition_area = union_of_dod_and_simulated_dz_mesh.loc[lambda x: x["dz_sim"] == "deposition"]
    return sum(selection_of_deposition_area["volume"])
