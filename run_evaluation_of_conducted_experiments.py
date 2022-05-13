import json
import os
from typing import NamedTuple

import pandas as pd
from geopandas import GeoDataFrame
from tqdm import tqdm

from csv_logging.calculate_entries import (
    goodness_of_fit_for_bottom_elevation,
    goodness_of_fit_for_velocity,
    goodness_of_fit_for_water_depth,
    goodness_of_fit_for_three_d_analysis,
)
from csv_logging.csvlogger import (
    CSVLogger,
    GoodnessOfFitForInitialVelocity,
    GoodnessOfFitForInitialBottomElevation,
    GoodnessOfFitForInitialWaterDepth,
    GoodnessOfFitFor3dEvaluation,
)
from evaluation_runner.analysis.three_dimensional import (
    create_union_of_dod_and_simulated_dz_mesh,
    clip_mesh_with_polygons,
)
from evaluation_runner.profiles.evaluate_profiles import (
    create_histogram_with_mesh_values,
    evaluate_points_along_profiles,
)
from extract_data.create_shape_files_from_simulation_results import process_h5_files_to_shape_files
from extract_data.summarising_mesh import (
    create_default_state_to_name_in_shape_file_mapping,
    create_summarising_mesh_with_all_results,
    assign_requested_values_from_summarising_mesh_to_point,
)
from profile_creation.containers import BeforeOrAfterFloodScenario
from script_for_profile_creation import create_paths
from utils.loading import load_data_with_crs_2056


def get_json_with_all_result_paths(path_to_all_experiments_to_evaluate: str) -> list[str]:
    with open(path_to_all_experiments_to_evaluate, "r") as json_file:
        return list(json.load(json_file))


def evaluate_simulation_on_given_points(
        path_to_all_experiments_to_evaluate: str,
        evaluation_points: GeoDataFrame,
        path_to_mesh: str,
        mapping: dict,
        flood_scenario: BeforeOrAfterFloodScenario,
        path_to_dod_as_polygon: str,
        paths_to_polygon_as_area_of_interest: tuple[str, ...],
        path_to_folder_containing_points_with_lines: str,
        simulation_time_in_seconds: int,
):
    logger_goodness_of_fit_for_bottom_elevation = CSVLogger(GoodnessOfFitForInitialBottomElevation)
    logger_goodness_of_fit_for_water_depth = CSVLogger(GoodnessOfFitForInitialWaterDepth)
    logger_goodness_of_fit_for_velocity = CSVLogger(GoodnessOfFitForInitialVelocity)
    logger_goodness_of_fit_for_three_d_evaluation = CSVLogger(GoodnessOfFitFor3dEvaluation)

    logger_triple = GpsPointsLoggerTriple(
        logger_goodness_of_fit_for_velocity=logger_goodness_of_fit_for_velocity,
        logger_goodness_of_fit_for_water_depth=logger_goodness_of_fit_for_water_depth,
        logger_goodness_of_fit_for_bottom_elevation=logger_goodness_of_fit_for_bottom_elevation,
    )

    all_paths_to_experiment_results = get_json_with_all_result_paths(path_to_all_experiments_to_evaluate)
    state_to_name_in_shape_file_mapping = create_default_state_to_name_in_shape_file_mapping(
        simulation_time_in_seconds=simulation_time_in_seconds)

    # mapping = {"bot_ele": "bot_ele_t0", "wse": "wse_t0", "v": "v_t0", "wd": "wd_t0"}
    for path in all_paths_to_experiment_results:
        experiment_id = os.path.split(path)[-1]
        resulting_geo_data_frames = process_h5_files_to_shape_files(path, path_to_mesh=path_to_mesh, time_step=300)
        summarising_mesh = create_summarising_mesh_with_all_results(
            resulting_geo_data_frames, state_to_name_in_shape_file_mapping
        ).rename(columns={v: k for k, v in mapping.items()})

        if do_points := True:
            renamed_updated_gps_points = assign_requested_values_from_summarising_mesh_to_point(
                list(mapping.keys()), summarising_mesh, points=evaluation_points.copy(deep=True)
            )

            logger_triple = calculate_and_log_statistics_for_gps_points(
                renamed_updated_gps_points, logger_triple, experiment_id=experiment_id, flood_scenario=flood_scenario
            )

            write_logs_for_gps_points(
                logger_triple,
                flood_scenario=flood_scenario,
            )

        if do_profiles := True:
            evaluate_points_along_profiles(
                mesh_with_all_results=summarising_mesh,
                flood_scenario=flood_scenario,
                path_to_folder_containing_points_with_line=path_to_folder_containing_points_with_lines,
                columns_to_lookup=list(mapping.keys()),
                experiment_id=experiment_id,
            )

        if do_polygons := True:
            union_of_dod_and_simulated_dz_mesh = create_union_of_dod_and_simulated_dz_mesh(
                path_to_dod_as_polygon=path_to_dod_as_polygon,
                mesh_with_all_results=summarising_mesh,
            )

            all_polygons = dict()
            for polygon_path in tqdm(paths_to_polygon_as_area_of_interest):
                masking_polygons_for_evaluation = load_data_with_crs_2056(polygon_path)
                polygon_name = os.path.split(polygon_path)[-1].split(".")[0]
                clipped_mesh = clip_mesh_with_polygons(
                    union_of_dod_and_simulated_dz_mesh, masking_polygons_for_evaluation, experiment_id=experiment_id
                )
                logger_goodness_of_fit_for_three_d_evaluation = calculate_and_log_3d_statistics_for_polygons(
                    logger_goodness_of_fit_for_three_d_evaluation,
                    union_of_dod_and_simulated_dz_mesh=clipped_mesh,
                    experiment_id=experiment_id,
                    polygon_name=polygon_name,
                )
                all_polygons[polygon_name] = masking_polygons_for_evaluation

            all_masking_polygons = pd.concat(all_polygons.values())
            clipped_mesh = clip_mesh_with_polygons(union_of_dod_and_simulated_dz_mesh, all_masking_polygons,
                                                   experiment_id)
            logger_goodness_of_fit_for_three_d_evaluation = calculate_and_log_3d_statistics_for_polygons(
                logger_goodness_of_fit_for_three_d_evaluation,
                union_of_dod_and_simulated_dz_mesh=clipped_mesh,
                experiment_id=experiment_id,
                polygon_name="-".join(all_polygons.keys()),
            )
            file_path = f"out\\polygons\\{flood_scenario.value}_{experiment_id}\\"
            if not os.path.exists(file_path):
                os.mkdir(file_path)

            file_name = "elevation_change.shp"
            clipped_mesh.to_file(file_path + file_name)

            write_log_for_3d_evaluation(
                logger_goodness_of_fit_for_three_d_evaluation=logger_goodness_of_fit_for_three_d_evaluation,
                flood_scenario=flood_scenario,
            )


class GpsPointsLoggerTriple(NamedTuple):
    logger_goodness_of_fit_for_velocity: CSVLogger
    logger_goodness_of_fit_for_water_depth: CSVLogger
    logger_goodness_of_fit_for_bottom_elevation: CSVLogger


def calculate_and_log_3d_statistics_for_polygons(
        logger_goodness_of_fit_for_three_d_evaluation: CSVLogger,
        union_of_dod_and_simulated_dz_mesh: GeoDataFrame,
        experiment_id: str,
        polygon_name,
) -> CSVLogger:
    logger_goodness_of_fit_for_three_d_evaluation.add_entry_to_log(
        goodness_of_fit_for_three_d_analysis(union_of_dod_and_simulated_dz_mesh, experiment_id, polygon_name)
    )
    return logger_goodness_of_fit_for_three_d_evaluation


def calculate_and_log_statistics_for_gps_points(
        renamed_updated_gps_points: GeoDataFrame, logger_triple: GpsPointsLoggerTriple, experiment_id, flood_scenario
) -> GpsPointsLoggerTriple:
    renamed_updated_gps_points["wd_sim_gps"] = renamed_updated_gps_points["wd"] - renamed_updated_gps_points["WT_m_"]
    gps_points_with_velocity: GeoDataFrame = (
        renamed_updated_gps_points.loc[renamed_updated_gps_points["Vel__m_s_"] > 0, :]
    ).copy(deep=True)
    gps_points_with_velocity["v_sim_gps"] = gps_points_with_velocity["v"] - gps_points_with_velocity["Vel__m_s_"]

    create_histogram_with_mesh_values(
        renamed_updated_gps_points, "wd_sim_gps", flood_scenario=flood_scenario, experiment_id=experiment_id
    )
    create_histogram_with_mesh_values(
        gps_points_with_velocity, "v_sim_gps", flood_scenario=flood_scenario, experiment_id=experiment_id
    )

    logger_triple.logger_goodness_of_fit_for_water_depth.add_entry_to_log(
        goodness_of_fit_for_water_depth(renamed_updated_gps_points, experiment_id=experiment_id)
    )
    logger_triple.logger_goodness_of_fit_for_velocity.add_entry_to_log(
        goodness_of_fit_for_velocity(gps_points_with_velocity, experiment_id=experiment_id)
    )
    logger_triple.logger_goodness_of_fit_for_bottom_elevation.add_entry_to_log(
        goodness_of_fit_for_bottom_elevation(renamed_updated_gps_points, experiment_id=experiment_id)
    )
    return logger_triple


def write_logs_for_gps_points(
        logger_triple: GpsPointsLoggerTriple,
        flood_scenario: BeforeOrAfterFloodScenario,
) -> None:
    logger_triple.logger_goodness_of_fit_for_velocity.write_logs_as_csv_to_file(
        f"log_goodness_of_fit_{flood_scenario}_velocities.csv"
    )
    logger_triple.logger_goodness_of_fit_for_water_depth.write_logs_as_csv_to_file(
        f"log_goodness_of_fit_{flood_scenario}_water_depths.csv"
    )
    logger_triple.logger_goodness_of_fit_for_bottom_elevation.write_logs_as_csv_to_file(
        f"log_goodness_of_fit_{flood_scenario}_bottom_ele.csv"
    )


def write_log_for_3d_evaluation(
        logger_goodness_of_fit_for_three_d_evaluation: CSVLogger, flood_scenario: BeforeOrAfterFloodScenario
) -> None:
    logger_goodness_of_fit_for_three_d_evaluation.write_logs_as_csv_to_file(
        f"log_three_d_statistics_{flood_scenario}.csv"
    )


def main():
    flood_scenario = BeforeOrAfterFloodScenario.af_2020
    simulation_time_in_seconds = 9000

    path_to_gps_points = create_paths(flood_scenario).path_to_gps_points
    #old mesh: path_to_mesh = r"C:\Users\nflue\Documents\Masterarbeit\02_Data\04_Model_220309\04_Model\01_input_data_old\BF2020_Mesh\new_mesh_all_inputs\bathymetry_and_mesh_BF2020_computational-mesh.2dm"
    path_to_mesh = r"C:\Users\nflue\Documents\Masterarbeit\02_Data\04_Model_220309\04_Model\01_input_data_new_def\BF2020_Mesh\new_mesh_all_inputs\Project1_computational-mesh_new_regions.2dm"
    paths_to_polygon_as_area_of_interest = (
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\side_channel_island.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\main_channel_island.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\begin_island.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\end_island.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\main_channel.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\gravel_bar.shp",
    )
    path_to_dod_as_polygon = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\DoDs\\dod_v2\\dod_af20_min_bf20_reclass_as_polygon_v2.shp"
    path_to_folder_containing_points_with_lines = "C:\\Users\\nflue\\Documents\\Masterarbeit\\03_Projects\\MasterThesis\\BasementPreparation\\river_profiles_from_bathymetry"

    paths_to_json_with_experiment_paths = r"C:\Users\nflue\Desktop\experiments\experiments\experiment_with_changed_lateral_slope_dtime_300\paths_to_experiments.json"

    if flood_scenario == BeforeOrAfterFloodScenario.bf_2020:
        mapping = {"bot_ele": "bot_ele_t0", "wse": "wse_t0", "v": "v_t0", "wd": "wd_t0"}

    elif flood_scenario == BeforeOrAfterFloodScenario.af_2020:
        mapping = {
            "bot_ele": "bot_ele_end",
            "wse": "wse_end",
            "v": "v_end",
            "wd": "wd_end",
            "delta_z": "delta_z",
            "volume": "volume",
        }
    else:
        raise NotImplementedError

    evaluate_simulation_on_given_points(
        paths_to_json_with_experiment_paths,
        load_data_with_crs_2056(path_to_gps_points),
        path_to_mesh=path_to_mesh,
        mapping=mapping,
        flood_scenario=flood_scenario,
        paths_to_polygon_as_area_of_interest=paths_to_polygon_as_area_of_interest,
        path_to_dod_as_polygon=path_to_dod_as_polygon,
        path_to_folder_containing_points_with_lines=path_to_folder_containing_points_with_lines,
        simulation_time_in_seconds=simulation_time_in_seconds
    )


if __name__ == "__main__":
    main()
