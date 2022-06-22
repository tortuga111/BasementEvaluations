from dataclasses import dataclass

import geopandas as gpd
from geopandas import GeoDataFrame

from csv_logging.csvlogger import CSVLogger, ScenarioEvaluationHmid
from evaluation_runner.scenario_evaluation.shield_stress import (
    ParametersForShearStressEvaluation,
    calculate_area_where_flow_velocity_and_water_depth_are_too_small,
)
from extract_data.summarising_mesh import StateToNameInShapeFileMapping


def calculate_entries_for_hmid_log(
    experiment_id: str,
    time_step: float,
    evaluation_parameters: ParametersForShearStressEvaluation,
    state_to_name_in_shape_file_mapping: StateToNameInShapeFileMapping,
    mesh_with_simulation_state: gpd.GeoDataFrame,
) -> ScenarioEvaluationHmid:
    selection_where_flow_velocity_and_wd_are_too_small = (
        calculate_area_where_flow_velocity_and_water_depth_are_too_small(
            evaluation_parameters, mesh_with_simulation_state, state_to_name_in_shape_file_mapping
        )
    )

    water_depth_ = state_to_name_in_shape_file_mapping.water_depth.final_name
    velocity_ = state_to_name_in_shape_file_mapping.flow_velocity.final_name
    chezy_ = state_to_name_in_shape_file_mapping.chezy_coefficient.final_name

    water_depth_variability = (
        selection_where_flow_velocity_and_wd_are_too_small[water_depth_].std()
        / selection_where_flow_velocity_and_wd_are_too_small[water_depth_].mean()
    )
    flow_velocity_variability = (
        selection_where_flow_velocity_and_wd_are_too_small[velocity_].std()
        / selection_where_flow_velocity_and_wd_are_too_small[velocity_].mean()
    )
    hydro_morphological_index_of_diversity = (1 + flow_velocity_variability) ** 2 * (1 + water_depth_variability) ** 2

    return ScenarioEvaluationHmid(
        experiment_id=experiment_id,
        time_step=time_step,
        wetted_area=selection_where_flow_velocity_and_wd_are_too_small.area.sum(),
        water_depth_variability=water_depth_variability * 100,
        flow_velocity_variability=flow_velocity_variability * 100,
        hydro_morphological_index_of_diversity=hydro_morphological_index_of_diversity,
    )


def calculate_and_log_hmid_statistics(
    logger_hmid: CSVLogger,
    experiment_id: str,
    evaluation_parameters: ParametersForShearStressEvaluation,
    time_step: float,
    mesh_with_simulation_state: gpd.GeoDataFrame,
    state_to_name_in_shape_file_mapping: StateToNameInShapeFileMapping,
) -> CSVLogger:
    logger_hmid.add_entry_to_log(
        calculate_entries_for_hmid_log(
            experiment_id=experiment_id,
            evaluation_parameters=evaluation_parameters,
            time_step=time_step,
            mesh_with_simulation_state=mesh_with_simulation_state,
            state_to_name_in_shape_file_mapping=state_to_name_in_shape_file_mapping,
        )
    )
    return logger_hmid
