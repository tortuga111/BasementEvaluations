import warnings
from typing import NamedTuple, Iterable

import geopandas as gpd
import numpy as np
from tqdm import tqdm

from extract_data.create_shape_files_from_simulation_results import SimulationResultsShapes


class MappingPair(NamedTuple):
    raw_name: str
    final_name: str


class StateToNameInShapeFileMapping(NamedTuple):
    water_depth: MappingPair
    hydraulic_state: MappingPair
    bottom_elevation: MappingPair
    flow_velocity: MappingPair
    chezy_coefficient: MappingPair


def create_default_state_to_name_in_shape_file_mapping(
    simulation_time_in_seconds: int,
) -> StateToNameInShapeFileMapping:
    return StateToNameInShapeFileMapping(
        hydraulic_state=MappingPair(f"{simulation_time_in_seconds}-Value", f"wse_{simulation_time_in_seconds}"),
        bottom_elevation=MappingPair(
            f"{simulation_time_in_seconds}-BottomEl", f"bottom_el_{simulation_time_in_seconds}"
        ),
        flow_velocity=MappingPair(f"{simulation_time_in_seconds}-Value", f"v_{simulation_time_in_seconds}"),
        water_depth=MappingPair("f___", f"fwd_{simulation_time_in_seconds}"),
        chezy_coefficient=MappingPair(f"{simulation_time_in_seconds}-ChezyCoe", f"chezy_{simulation_time_in_seconds}"),
    )


def create_mesh_from_mapped_values(
    all_result_shapes: SimulationResultsShapes,
    mapping: StateToNameInShapeFileMapping,
) -> gpd.GeoDataFrame:
    bottom_elevation = all_result_shapes.bottom_elevation
    mesh_with_result = gpd.GeoDataFrame(geometry=bottom_elevation.geometry, crs=bottom_elevation.crs)
    mesh_with_result["material_index"] = bottom_elevation["material_index"]
    assert mesh_with_result.crs == 2056
    try:
        return calculate_mesh_entries_at_a_given_time(all_result_shapes, mapping, mesh_with_result)
    except KeyError as key_error:
        warnings.warn(f"Check the mapping in {mapping}, as you might have missed a column")
        raise key_error


def create_mesh_with_before_and_after_flood_data(
    all_result_shapes: SimulationResultsShapes,
    before_flood_mapping: StateToNameInShapeFileMapping,
    after_flood_mapping: StateToNameInShapeFileMapping,
) -> gpd.GeoDataFrame:
    mesh_with_results_before_flood = create_mesh_from_mapped_values(all_result_shapes, before_flood_mapping)
    mesh_with_results_after_flood = create_mesh_from_mapped_values(all_result_shapes, after_flood_mapping)
    joined_mesh = mesh_with_results_after_flood.join(mesh_with_results_before_flood, lsuffix="geometry")
    joined_mesh["delta_z"] = (
        mesh_with_results_after_flood[after_flood_mapping.bottom_elevation.final_name]
        - mesh_with_results_before_flood[before_flood_mapping.bottom_elevation.final_name]
    )
    return joined_mesh


def calculate_mesh_entries_at_a_given_time(
    all_result_shapes: SimulationResultsShapes,
    mapping: StateToNameInShapeFileMapping,
    mesh_with_all_results: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    mesh_with_all_results[mapping.water_depth.final_name] = (
        all_result_shapes.hydraulic_state[mapping.hydraulic_state.raw_name]
        - all_result_shapes.bottom_elevation[mapping.bottom_elevation.raw_name]
    )
    mesh_with_all_results[mapping.flow_velocity.final_name] = all_result_shapes.absolute_flow_velocity[
        mapping.flow_velocity.raw_name
    ]
    mesh_with_all_results[mapping.bottom_elevation.final_name] = all_result_shapes.bottom_elevation[
        mapping.bottom_elevation.raw_name
    ]
    mesh_with_all_results[mapping.hydraulic_state.final_name] = all_result_shapes.hydraulic_state[
        mapping.hydraulic_state.raw_name
    ]
    mesh_with_all_results[mapping.chezy_coefficient.final_name] = all_result_shapes.chezy_coefficient[
        mapping.chezy_coefficient.raw_name
    ]
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
