import os.path
from typing import Iterable, NamedTuple, Sequence

import geopandas as gpd
import h5py
import py2dm
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
from tqdm import tqdm

from helpers.global_and_constant_values import GlobalConstants
from helpers.helpers import change_back_to_original_wd_afterwards
from simulation_configuration import get_experiment_base_run_root_folder
from simulation_runner.prepare_basement.preparation import (
    get_root_directory_for_experiment_results,
    load_paths_to_experiment_results,
)


def load_paths_to_results() -> tuple[str, ...]:
    experiment_base_run_root_folder = get_experiment_base_run_root_folder()
    experiment_results_root_directory = get_root_directory_for_experiment_results(experiment_base_run_root_folder)
    return load_paths_to_experiment_results(experiment_results_root_directory)


def extract_data_for_evaluation(path_to_root_directory: str) -> str:
    return path_to_root_directory


class SimulationResultsShapeFilePaths(NamedTuple):
    path_to_bottom_elevation: str
    path_to_hydraulic_state: str
    path_to_flow_velocity: str
    path_to_absolute_flow_velocity: str


class SimulationResultsShapes(NamedTuple):
    bottom_elevation: gpd.GeoDataFrame
    hydraulic_state: gpd.GeoDataFrame
    flow_velocity: gpd.GeoDataFrame
    absolute_flow_velocity: gpd.GeoDataFrame


def append_constant_data_per_time_step_to_geo_data_frame(
    base_data_frame: GeoDataFrame, file_with_constant_1d_data: h5py.File, column_name: str, time_steps: Sequence[int]
) -> GeoDataFrame:
    data_frame_to_fill = base_data_frame.copy(deep=True)
    for time_step in tqdm(time_steps):
        column_key = f"{time_step}-{column_name}"
        data_frame_to_fill[column_key] = file_with_constant_1d_data
    return data_frame_to_fill


def process_h5_files_to_shape_files(
    path_to_root_directory: str, path_to_mesh: str, time_step: int, used_geomorphologic_module: bool
) -> SimulationResultsShapes:
    path_to_results = os.path.join(path_to_root_directory, "evaluation")
    if not os.path.exists(path_to_results):
        os.mkdir(path_to_results)
    triangle_polygons = []
    with py2dm.Reader(path_to_mesh) as mesh:
        nodes = {node.id: node for i, node in enumerate(mesh.nodes)}
        for element in tqdm(mesh.elements):
            point_indices = element.nodes
            triangle_polygons.append(Polygon([nodes[point_index].pos for point_index in point_indices]))
    base_data_frame = GeoDataFrame(geometry=triangle_polygons, crs=2056)

    with change_back_to_original_wd_afterwards(path_to_results):
        h5_path = os.path.join(path_to_root_directory, GlobalConstants.results_h5_file_name)
        h5_results_data = h5py.File(h5_path, "r")

        hydraulic_state = append_time_series_data_to_geo_data_frame(
            base_data_frame,
            h5_results_data["RESULTS/CellsAll/HydState"],
            ["Value", "DX", "DY"],
        )
        h5_path = os.path.join(path_to_root_directory, "results_aux.h5")
        h5_auxiliary_data = h5py.File(h5_path, "r")
        flow_velocity = append_time_series_data_to_geo_data_frame(
            base_data_frame, h5_auxiliary_data["flow_velocity"], ["DX", "DY"]
        )
        absolute_flow_velocity = append_time_series_data_to_geo_data_frame(
            base_data_frame, h5_auxiliary_data["flow_velocity_abs"], ["Value"]
        )
        if used_geomorphologic_module:
            bottom_elevation = append_time_series_data_to_geo_data_frame(
                base_data_frame, h5_results_data["RESULTS/CellsAll/BottomEl"], ["BottomEl"]
            )
        else:
            time_steps = list(range(len(absolute_flow_velocity.columns) - 1))
            bottom_elevation = append_constant_data_per_time_step_to_geo_data_frame(
                base_data_frame, h5_results_data["CellsAll/BottomEl"], "BottomEl", time_steps
            )

    return rename_columns_to_represent_time_step(
        SimulationResultsShapes(
            bottom_elevation=bottom_elevation.copy(),
            hydraulic_state=hydraulic_state.copy(),
            flow_velocity=flow_velocity.copy(),
            absolute_flow_velocity=absolute_flow_velocity.copy(),
        ),
        time_step,
    )


def rename_columns_to_represent_time_step(result: SimulationResultsShapes, time_step: int) -> SimulationResultsShapes:
    relabeled_dataframes = []
    for dataframe in result:
        dataframe: GeoDataFrame
        mapping = {
            name: f"{int(name.split('-')[0]) * time_step}-{''.join(name.split('-')[1:])}"
            for name in dataframe.columns.values
            if "-" in name
        }
        relabeled_dataframes.append(dataframe.rename(columns=mapping))
    return SimulationResultsShapes(*relabeled_dataframes)


def append_time_series_data_to_geo_data_frame(
    base_data_frame: GeoDataFrame, file_with_1d_data_per_step: h5py.File, column_names: Iterable[str]
) -> GeoDataFrame:
    data_frame_to_fill = base_data_frame.copy(deep=True)
    for key in tqdm(sorted(file_with_1d_data_per_step.keys(), key=lambda x: int(x))):
        for column_index, column_name in enumerate(column_names):
            column_key = f"{key}-{column_name}"
            data_frame_to_fill[column_key] = file_with_1d_data_per_step[key][:, column_index]
    return data_frame_to_fill
    # data_frame_to_fill.to_file(f"{file_name}.shp" if not file_name.endswith(".shp") else file_name)
