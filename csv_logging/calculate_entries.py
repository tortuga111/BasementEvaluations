from geopandas import GeoDataFrame

from csv_logging.csvlogger import (
    GoodnessOfFitForInitialVelocity,
    GoodnessOfFitForInitialBottomElevation,
    GoodnessOfFitForInitialWaterDepth,
    GoodnessOfFitFor3dEvaluation,
)
from evaluation_runner.analysis.three_dimensional import (
    calculate_ratio_of_eroded_area_dod,
    calculate_ratio_of_deposited_area_dod,
    calculate_ratio_of_eroded_area_sim,
    calculate_ratio_of_deposited_area_sim,
    calculate_ratio_of_identical_change,
    calculate_ratio_of_different_change, calculate_eroded_volume, calculate_deposited_volume,
)
from misc.dataclasses_for_evaluations import ColumnNamePair
from statistical_formulas.formulas_goodness_of_fit import (
    calculate_index_of_agreement,
    calculate_nash_sutcliffe_efficiency,
    calculate_percent_bias,
    calculate_root_mean_square_error,
    calculate_mean_absolute_error,
    calculate_average_error,
)


def goodness_of_fit_for_velocity(gps_points_with_velocity, experiment_id: str) -> GoodnessOfFitForInitialVelocity:
    column_names_flow_velocity = ColumnNamePair(observed="Vel__m_s_", simulated="v")
    message_goodness_of_fit_initial_velocities = GoodnessOfFitForInitialVelocity(
        experiment_id=experiment_id,
        v_obs_mean=(gps_points_with_velocity["Vel__m_s_"].mean()),
        v_obs_std=(gps_points_with_velocity["Vel__m_s_"].std()),
        v_obs_min=(gps_points_with_velocity["Vel__m_s_"].min()),
        v_obs_max=(gps_points_with_velocity["Vel__m_s_"].max()),
        v_sim_mean=(gps_points_with_velocity["v"].mean()),
        v_sim_std=(gps_points_with_velocity["v"].std()),
        v_sim_min=(gps_points_with_velocity["v"].min()),
        v_sim_max=(gps_points_with_velocity["v"].max()),
        v_index_of_agreement=calculate_index_of_agreement(gps_points_with_velocity, column_names_flow_velocity),
        v_nash_sutcliffe_efficiency=(
            calculate_nash_sutcliffe_efficiency(gps_points_with_velocity, column_names_flow_velocity)
        ),
        v_percent_bias=(calculate_percent_bias(gps_points_with_velocity, column_names_flow_velocity)),
        v_root_mean_square_error=(
            calculate_root_mean_square_error(gps_points_with_velocity, column_names_flow_velocity)
        ),
        v_mean_absolute_error=(calculate_mean_absolute_error(gps_points_with_velocity, column_names_flow_velocity)),
        v_mean_error=(calculate_average_error(gps_points_with_velocity, column_names_flow_velocity)),
    )
    return message_goodness_of_fit_initial_velocities


def goodness_of_fit_for_bottom_elevation(
    updated_gps_points, experiment_id: str
) -> GoodnessOfFitForInitialBottomElevation:
    column_names_bottom_elevation = ColumnNamePair(observed="H", simulated="bot_ele")
    message_goodness_of_fit_initial_bottom_elevation = GoodnessOfFitForInitialBottomElevation(
        experiment_id=experiment_id,
        bot_ele_obs_mean=(updated_gps_points["H"].mean()),
        bot_ele_obs_std=(updated_gps_points["H"].std()),
        bot_ele_obs_min=(updated_gps_points["H"].min()),
        bot_ele_obs_max=(updated_gps_points["H"].max()),
        bot_ele_sim_mean=(updated_gps_points["bot_ele"].mean()),
        bot_ele_sim_std=(updated_gps_points["bot_ele"].std()),
        bot_ele_min=(updated_gps_points["bot_ele"].min()),
        bot_ele_max=(updated_gps_points["bot_ele"].max()),
        bot_ele_mean_error=(calculate_average_error(updated_gps_points, column_names_bottom_elevation)),
        bot_ele_mean_absolute_error=(calculate_mean_absolute_error(updated_gps_points, column_names_bottom_elevation)),
        bot_ele_root_mean_square_error=(
            calculate_root_mean_square_error(updated_gps_points, column_names_bottom_elevation)
        ),
        bot_ele_percent_bias=(calculate_percent_bias(updated_gps_points, column_names_bottom_elevation)),
        bot_ele_nash_sutcliffe_efficiency=(
            calculate_nash_sutcliffe_efficiency(updated_gps_points, column_names_bottom_elevation)
        ),
        bot_ele_index_of_agreement=calculate_index_of_agreement(updated_gps_points, column_names_bottom_elevation),
    )
    return message_goodness_of_fit_initial_bottom_elevation


def goodness_of_fit_for_water_depth(updated_gps_points, experiment_id: str) -> GoodnessOfFitForInitialWaterDepth:
    column_names_water_depth = ColumnNamePair(observed="WT_m_", simulated="wd")
    return GoodnessOfFitForInitialWaterDepth(
        experiment_id=experiment_id,
        wd_obs_mean=(updated_gps_points["WT_m_"].mean()),
        wd_obs_std=(updated_gps_points["WT_m_"].std()),
        wd_obs_min=(updated_gps_points["WT_m_"].min()),
        wd_obs_max=(updated_gps_points["WT_m_"].max()),
        wd_sim_mean=(updated_gps_points["wd"].mean()),
        wd_sim_std=(updated_gps_points["wd"].std()),
        wd_sim_min=(updated_gps_points["wd"].min()),
        wd_sim_max=(updated_gps_points["wd"].max()),
        wd_mean_error=(calculate_average_error(updated_gps_points, column_names_water_depth)),
        wd_mean_absolute_error=(calculate_mean_absolute_error(updated_gps_points, column_names_water_depth)),
        wd_root_mean_square_error=(calculate_root_mean_square_error(updated_gps_points, column_names_water_depth)),
        wd_percent_bias=(calculate_percent_bias(updated_gps_points, column_names_water_depth)),
        wd_nash_sutcliffe_efficiency=(
            calculate_nash_sutcliffe_efficiency(updated_gps_points, column_names_water_depth)
        ),
        wd_index_of_agreement=(calculate_index_of_agreement(updated_gps_points, column_names_water_depth)),
    )


def goodness_of_fit_for_three_d_analysis(
    union_of_dod_and_simulated_dz_mesh: GeoDataFrame, experiment_id: str, polygon_name: str
) -> GoodnessOfFitFor3dEvaluation:
    return GoodnessOfFitFor3dEvaluation(
        experiment_id=experiment_id,
        polygon_name=polygon_name,
        ratio_of_eroded_area_dod=calculate_ratio_of_eroded_area_dod(union_of_dod_and_simulated_dz_mesh),
        ratio_of_deposited_area_dod=calculate_ratio_of_deposited_area_dod(union_of_dod_and_simulated_dz_mesh),
        ratio_of_eroded_area_sim=calculate_ratio_of_eroded_area_sim(union_of_dod_and_simulated_dz_mesh),
        ratio_of_deposited_area_sim=calculate_ratio_of_deposited_area_sim(union_of_dod_and_simulated_dz_mesh),
        ratio_of_identical_change=calculate_ratio_of_identical_change(union_of_dod_and_simulated_dz_mesh),
        ratio_of_different_change=calculate_ratio_of_different_change(union_of_dod_and_simulated_dz_mesh),
        eroded_volume_sim=calculate_eroded_volume(union_of_dod_and_simulated_dz_mesh),
        deposited_volume_sim=calculate_deposited_volume(union_of_dod_and_simulated_dz_mesh),
    )
