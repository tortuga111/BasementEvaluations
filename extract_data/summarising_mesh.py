from typing import NamedTuple, Iterable

import geopandas as gpd
import numpy as np
from tqdm import tqdm

from extract_data.create_shape_files_from_simulation_results import SimulationResultsShapes


class StateToNameInShapeFileMapping(NamedTuple):
    hydraulic_state_t_0: str = "0000000-Va"
    bottom_elevation_t_0: str = "0000000-Bo"
    hydraulic_state_t_end: str = "0000003-Va"
    bottom_elevation_t_end: str = "0000003-Bo"
    flow_velocity_t_0: str = "0-Value"
    flow_velocity_t_end: str = "3-Value"


def create_default_state_to_name_in_shape_file_mapping(simulation_time_in_seconds: int) -> StateToNameInShapeFileMapping:
    return StateToNameInShapeFileMapping(
        hydraulic_state_t_0="0-Value",
        bottom_elevation_t_0="0-BottomEl",
        hydraulic_state_t_end=f"{simulation_time_in_seconds}-Value",
        bottom_elevation_t_end=f"{simulation_time_in_seconds}-BottomEl",
        flow_velocity_t_0="0-Value",
        flow_velocity_t_end=f"{simulation_time_in_seconds}-Value",
    )


def create_esri_style_state_to_name_in_shape_file_mapping() -> StateToNameInShapeFileMapping:
    return StateToNameInShapeFileMapping(
        hydraulic_state_t_0="0000000-Va",
        bottom_elevation_t_0="0000000-Bo",
        hydraulic_state_t_end="0000003-Va",
        bottom_elevation_t_end="0000003-Bo",
        flow_velocity_t_0="0-Value",
        flow_velocity_t_end="3-Value",
    )


def create_summarising_mesh_with_all_results(
    all_result_shapes: SimulationResultsShapes, mapping: StateToNameInShapeFileMapping
) -> gpd.GeoDataFrame:
    bottom_elevation, hydraulic_state, flow_velocity, absolute_flow_velocity = all_result_shapes
    mesh_with_all_results = gpd.GeoDataFrame(geometry=bottom_elevation.geometry, crs=bottom_elevation.crs)
    assert mesh_with_all_results.crs == 2056

    try:
        # before flood
        mesh_with_all_results["wd_t0"] = (
            hydraulic_state[mapping.hydraulic_state_t_0] - bottom_elevation[mapping.bottom_elevation_t_0]
        )
        mesh_with_all_results["v_t0"] = absolute_flow_velocity[mapping.flow_velocity_t_0]
        mesh_with_all_results["wse_t0"] = hydraulic_state[mapping.hydraulic_state_t_0]
        mesh_with_all_results["bot_ele_t0"] = bottom_elevation[mapping.bottom_elevation_t_0]
        # after flood
        mesh_with_all_results["wd_end"] = (
            hydraulic_state[mapping.hydraulic_state_t_end] - bottom_elevation[mapping.bottom_elevation_t_end]
        )
        mesh_with_all_results["delta_z"] = (
            bottom_elevation[mapping.bottom_elevation_t_end] - bottom_elevation[mapping.bottom_elevation_t_0]
        )
        mesh_with_all_results["v_end"] = absolute_flow_velocity[mapping.flow_velocity_t_end]
        mesh_with_all_results["bot_ele_end"] = bottom_elevation[mapping.bottom_elevation_t_end]
        mesh_with_all_results["wse_end"] = hydraulic_state[mapping.hydraulic_state_t_end]

    except KeyError as key_error:
        print(f"Check the mapping in {mapping}, as you might have missed a column")
        raise key_error
    return mesh_with_all_results


def assign_requested_values_from_summarising_mesh_to_point(
    columns_to_lookup: Iterable[str], mesh_with_all_results: gpd.GeoDataFrame, points: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    column_values = [[] for _ in columns_to_lookup]
    for index, point in tqdm(list(enumerate(points.geometry))):
        _contains = mesh_with_all_results.contains(point)
        if not any(_contains):
            for column_index, _ in enumerate(columns_to_lookup):
                column_values[column_index].append(np.nan)
        else:
            for column_index, column_name in enumerate(columns_to_lookup):
                value = mesh_with_all_results.loc[_contains, column_name].values[0]
                column_values[column_index].append(value)
    for column_values, column_name in zip(column_values, columns_to_lookup):
        points[column_name] = column_values
    return points
