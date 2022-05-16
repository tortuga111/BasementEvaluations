from dataclasses import dataclass

import geopandas as gpd
from geopandas import GeoDataFrame

@dataclass(frozen=True)
class ParametersForScenarioEvaluation:
    density_water: float
    gravity: float
    k_strickler: float
    density_gravel: float
    threshold_water_depth: float
    threshold_flow_velocity: float
    diameter_50: float
    diameter_90: float
    critical_shield_stress: float

def calculate_guenter_criterion(diameter_90: float, diameter_50: float) -> float:
    return 0.05 * (diameter_90 / diameter_50) ** (2 / 3)


def create_parameters_for_shear_stress() -> ParametersForScenarioEvaluation:
    return ParametersForScenarioEvaluation(
        density_water=1000,
        density_gravel=2650,
        gravity=9.81,
        k_strickler=30.4,
        threshold_water_depth=0.1,
        threshold_flow_velocity=0.01,
        diameter_90=11.3,
        diameter_50=5.7,
        critical_shield_stress=0.047)


def calculate_area_where_critical_shear_stress_is_reached_for_every_timestep(mesh_with_all_results: gpd.GeoDataFrame,
                                                                             density_water: float, gravity: float,
                                                                             k_strickler: float, density_gravel: float,
                                                                             threshold_water_depth: float,
                                                                             threshold_flow_velocity: float,
                                                                             diameter_50: float,
                                                                             diameter_90: float,
                                                                             critical_shield_stress: float):

    for timestep in mesh_with_all_results:
        selection_where_wd_and_v_too_small = select_areas_where_waterdepht_and_velocity_are_more_than_threshold(
            mesh_with_all_results, threshold_flow_velocity, threshold_water_depth)

        calculate_tau(density_water, gravity, k_strickler, mesh_with_all_results, selection_where_wd_and_v_too_small)
        selection_where_wd_and_v_too_small["theta"] = (mesh_with_all_results["tau"] / ((density_gravel - density_water) * gravity * diameter_50))

        calculate_area_where_theta_critical_is_reached(critical_shield_stress, selection_where_wd_and_v_too_small)

        selection_where_guenter_criterion_is_reached: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
            selection_where_wd_and_v_too_small["theta"] > calculate_guenter_criterion(diameter_50=diameter_50,
                                                                                       diameter_90=diameter_90)]

        area_where_guenter_criterion_is_reached: float = sum(selection_where_guenter_criterion_is_reached.area)


def calculate_area_where_theta_critical_is_reached(critical_shield_stress, selection_where_wd_and_v_too_small) -> float:
    selection_where_theta_critical_is_reached: GeoDataFrame = selection_where_wd_and_v_too_small.loc[
        selection_where_wd_and_v_too_small["theta"] > critical_shield_stress]
    area_where_tau_critical_is_reached: float = sum(selection_where_theta_critical_is_reached.area)
    return area_where_tau_critical_is_reached


def calculate_tau(density_water, gravity, k_strickler, mesh_with_all_results, selection_where_wd_and_v_too_small):
    selection_where_wd_and_v_too_small["tau"] = (density_water * gravity * mesh_with_all_results["v"] ** 2 * (
            k_strickler ** -1) ** 2) / (mesh_with_all_results["wd"] ** (1 / 3))


def select_areas_where_waterdepht_and_velocity_are_more_than_threshold(mesh_with_all_results, threshold_flow_velocity,
                                                                       threshold_water_depth):
    condition_wd_and_v_too_small = (mesh_with_all_results["v"] >= threshold_flow_velocity) & (
            mesh_with_all_results["wd"] >= threshold_water_depth)
    selection_where_wd_and_v_too_small: GeoDataFrame = mesh_with_all_results.loc[condition_wd_and_v_too_small]
    return selection_where_wd_and_v_too_small


