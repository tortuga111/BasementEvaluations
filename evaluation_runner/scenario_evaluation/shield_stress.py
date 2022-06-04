from dataclasses import dataclass

import geopandas as gpd
from geopandas import GeoDataFrame

from csv_logging.csvlogger import CSVLogger, ShearStress
from extract_data.summarising_mesh import StateToNameInShapeFileMapping


@dataclass(frozen=True)
class ParametersForShearStressEvaluation:
    density_water: float
    gravity: float
    k_strickler: float
    density_gravel: float
    threshold_water_depth: float
    threshold_flow_velocity: float
    diameter_50: float
    diameter_90: float
    critical_shield_stress: float


def create_parameters_for_shear_stress() -> ParametersForShearStressEvaluation:
    return ParametersForShearStressEvaluation(
        density_water=1000,
        density_gravel=2650,
        gravity=9.81,
        k_strickler=34,
        threshold_water_depth=0.01,
        threshold_flow_velocity=0.01,
        diameter_90=0.113,
        diameter_50=0.057,
        critical_shield_stress=0.047,
    )


def _calculate_guenter_criterion(diameter_90: float, diameter_50: float) -> float:
    return 0.05 * ((diameter_90 / diameter_50) ** (2 / 3))


def calculate_area_where_flow_velocity_and_water_depth_are_too_small(
        mesh_with_simulation_state: gpd.GeoDataFrame,
        evaluation_parameters: ParametersForShearStressEvaluation,
        state_to_name_in_shape_file_mapping: StateToNameInShapeFileMapping,
) -> gpd.GeoDataFrame:
    water_depth_ = state_to_name_in_shape_file_mapping.water_depth.final_name
    velocity_ = state_to_name_in_shape_file_mapping.flow_velocity.final_name
    chezy_ = state_to_name_in_shape_file_mapping.chezy_coefficient.final_name
    condition_wd_and_v_too_small = (
                                           mesh_with_simulation_state[
                                               velocity_] >= evaluation_parameters.threshold_flow_velocity
                                   ) & (mesh_with_simulation_state[
                                            water_depth_] >= evaluation_parameters.threshold_water_depth)
    small: GeoDataFrame = mesh_with_simulation_state.loc[condition_wd_and_v_too_small]
    selection_where_wd_and_v_too_small = small.copy()

    _constant_component = (
            evaluation_parameters.density_water
            * evaluation_parameters.gravity
            * (1 / evaluation_parameters.k_strickler) ** 2
    )
    dimensionless_cf_squared_with_power_law = selection_where_wd_and_v_too_small[water_depth_] ** (
            1 / 3) / evaluation_parameters.gravity * (evaluation_parameters.k_strickler) ** 2
    selection_where_wd_and_v_too_small["tau"] = None
    selection_where_wd_and_v_too_small["tau"] = (evaluation_parameters.density_water *
                                                 selection_where_wd_and_v_too_small[
                                                     velocity_] ** 2) / dimensionless_cf_squared_with_power_law

    selection_where_wd_and_v_too_small["tau_chezy"] = None
    selection_where_wd_and_v_too_small["tau_chezy"] = (
                                                              evaluation_parameters.density_water
                                                              * selection_where_wd_and_v_too_small[velocity_] ** 2) / \
                                                      selection_where_wd_and_v_too_small[chezy_]

    selection_where_wd_and_v_too_small["theta"] = None
    selection_where_wd_and_v_too_small["theta"] = selection_where_wd_and_v_too_small["tau"] / (
            (evaluation_parameters.density_gravel - evaluation_parameters.density_water)
            * evaluation_parameters.gravity
            * evaluation_parameters.diameter_50
    )

    selection_where_wd_and_v_too_small["theta_chez"] = None
    selection_where_wd_and_v_too_small["theta_chez"] = selection_where_wd_and_v_too_small["tau_chezy"] / (
            (evaluation_parameters.density_gravel - evaluation_parameters.density_water)
            * evaluation_parameters.gravity
            * evaluation_parameters.diameter_50
    )
    return selection_where_wd_and_v_too_small


def select_area_where_guenter_criterion_is_reached(
        selection_where_wd_and_v_too_small: gpd.GeoDataFrame, evaluation_parameters: ParametersForShearStressEvaluation
) -> gpd.GeoDataFrame:
    selection_where_guenter_criterion_is_reached: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
        selection_where_wd_and_v_too_small["theta"]
        > _calculate_guenter_criterion(
            diameter_50=evaluation_parameters.diameter_50, diameter_90=evaluation_parameters.diameter_90
        )
        ]
    return selection_where_guenter_criterion_is_reached


def select_area_where_guenter_criterion_is_reached_chezy(
        selection_where_wd_and_v_too_small: gpd.GeoDataFrame, evaluation_parameters: ParametersForShearStressEvaluation
) -> gpd.GeoDataFrame:
    selection_where_guenter_criterion_is_reached_chezy: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
        selection_where_wd_and_v_too_small["theta_chez"]
        > _calculate_guenter_criterion(
            diameter_50=evaluation_parameters.diameter_50, diameter_90=evaluation_parameters.diameter_90
        )
        ]
    return selection_where_guenter_criterion_is_reached_chezy


def select_area_where_crit_tau_is_reached(selection_where_wd_and_v_too_small: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    selection_where_critical_tau_is_reached: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
        selection_where_wd_and_v_too_small["tau"] >= 50]
    return selection_where_critical_tau_is_reached


def select_area_where_crit_shield_stress_is_reached(
        selection_where_wd_and_v_too_small: gpd.GeoDataFrame, evaluation_parameters: ParametersForShearStressEvaluation
) -> gpd.GeoDataFrame:
    selection_where_theta_critical_is_reached_chezy: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
        selection_where_wd_and_v_too_small["theta"] >= evaluation_parameters.critical_shield_stress
        ]
    return selection_where_theta_critical_is_reached_chezy


def select_area_where_crit_shield_stress_is_reached_with_chezy(
        selection_where_wd_and_v_too_small: gpd.GeoDataFrame, evaluation_parameters: ParametersForShearStressEvaluation
) -> gpd.GeoDataFrame:
    selection_where_theta_critical_is_reached: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
        selection_where_wd_and_v_too_small["theta_chez"] >= evaluation_parameters.critical_shield_stress
        ]
    return selection_where_theta_critical_is_reached


def calculate_and_log_shear_stress_statistics(
        logger_shear_stress: CSVLogger,
        experiment_id: str,
        evaluation_parameters: ParametersForShearStressEvaluation,
        time_step: float,
        selection_where_wd_and_v_too_small: gpd.GeoDataFrame,
) -> CSVLogger:
    logger_shear_stress.add_entry_to_log(
        calculate_entries_for_shear_stress_log(
            experiment_id=experiment_id,
            evaluation_parameters=evaluation_parameters,
            time_step=time_step,
            selection_where_wd_and_v_too_small=selection_where_wd_and_v_too_small,
        )
    )
    return logger_shear_stress


def calculate_entries_for_shear_stress_log(
        experiment_id: str,
        time_step: float,
        selection_where_wd_and_v_too_small: gpd.GeoDataFrame,
        evaluation_parameters: ParametersForShearStressEvaluation,
) -> ShearStress:
    return ShearStress(
        experiment_id=experiment_id,
        time_step=time_step,
        discharge=time_step / 270,
        wetted_area=sum(selection_where_wd_and_v_too_small.area),
        abs_area_tau_more_than_50Nm=select_area_where_crit_tau_is_reached(
            selection_where_wd_and_v_too_small).area.sum(),
        rel_area_tau_more_than_50Nm=select_area_where_crit_tau_is_reached(
            selection_where_wd_and_v_too_small).area.sum() / selection_where_wd_and_v_too_small.area.sum(),
        abs_area_critical_shield_stress=select_area_where_crit_shield_stress_is_reached(
            selection_where_wd_and_v_too_small,
            evaluation_parameters=evaluation_parameters,
        ).area.sum(),
        area_guenter_criterion=select_area_where_guenter_criterion_is_reached(
            selection_where_wd_and_v_too_small, evaluation_parameters,
        ).area.sum(),
        rel_area_critical_shield_stress=(select_area_where_crit_shield_stress_is_reached(
            selection_where_wd_and_v_too_small,
            evaluation_parameters=evaluation_parameters,
        )).area.sum()
                                        / selection_where_wd_and_v_too_small.area.sum(),
        rel_area_guenter_criterion=select_area_where_guenter_criterion_is_reached(
            selection_where_wd_and_v_too_small,
            evaluation_parameters=evaluation_parameters,
        ).area.sum()
                                   / selection_where_wd_and_v_too_small.area.sum(),
        abs_area_critical_shield_stress_chezy=select_area_where_crit_shield_stress_is_reached_with_chezy(
            selection_where_wd_and_v_too_small, evaluation_parameters=evaluation_parameters,
        ).area.sum(),
        area_guenter_criterion_chezy=select_area_where_guenter_criterion_is_reached_chezy(
            selection_where_wd_and_v_too_small, evaluation_parameters=evaluation_parameters,
        ).area.sum(),
        rel_area_critical_shield_stress_chezy=(
                                                  select_area_where_crit_shield_stress_is_reached_with_chezy(
                                                      selection_where_wd_and_v_too_small,
                                                      evaluation_parameters=evaluation_parameters,
                                                  ).area.sum()
                                              )
                                              / selection_where_wd_and_v_too_small.area.sum(),
        rel_area_guenter_criterion_chezy=(
                                             select_area_where_guenter_criterion_is_reached_chezy(
                                                 selection_where_wd_and_v_too_small,
                                                 evaluation_parameters=evaluation_parameters,
                                             ).area.sum()
                                         )
                                         / selection_where_wd_and_v_too_small.area.sum(),
    )
