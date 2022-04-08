import glob
import pickle
from typing import Iterable

import geopandas as gpd
import numpy as np
from plotly import graph_objs as go
from tqdm import tqdm

from script_for_profile_creation import (
    OrderedProjectedGpsPointsPerProfileLine,
    BeforeOrAfterFloodScenario,
    create_z_column_name,
)
from utils.loading import load_data_with_crs_2056

def load_data_from_simulations():
    path_to_bottom_elevation = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\06_test_run_hw20_new_mesh\\discharge_file@hydrograph_continue_HW20_plus2_5pc.txt$default_friction@35.0$end@1000\\evaluation\\bottom_elevation.shp"
    path_to_hydraulic_state = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\06_test_run_hw20_new_mesh\\discharge_file@hydrograph_continue_HW20_plus2_5pc.txt$default_friction@35.0$end@1000\\evaluation\\hydraulic_state.shp"
    path_to_flow_velocity = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\06_test_run_hw20_new_mesh\\discharge_file@hydrograph_continue_HW20_plus2_5pc.txt$default_friction@35.0$end@1000\\evaluation\\flow_velocity_abs.shp"
    path_to_gps_points_bf20 = (
        r"C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\BF2020\\GPS_transects_BF2020_selection.shp"
    )
    gps_points_bf20 = load_data_with_crs_2056(path_to_gps_points_bf20)
    bottom_elevation = load_data_with_crs_2056(path_to_bottom_elevation)
    hydraulic_state = load_data_with_crs_2056(path_to_hydraulic_state)
    flow_velocity = load_data_with_crs_2056(path_to_flow_velocity)
    return bottom_elevation, flow_velocity, gps_points_bf20, hydraulic_state


def main():
    bottom_elevation, flow_velocity, gps_points_bf20, hydraulic_state = load_data_from_simulations()

    mesh_with_all_results = create_summarising_mesh_with_all_results(bottom_elevation, flow_velocity, hydraulic_state)


    simulated_water_depth = []
    for index, point in tqdm(enumerate(gps_points_bf20.geometry)):
        contains = mesh_with_all_results.contains(point)
        if not any(contains):
            simulated_water_depth.append(np.nan)
        else:
            value = mesh_with_all_results.loc[contains, "wd_t0"].values[0]
            simulated_water_depth.append(value)
    gps_points_bf20["sim_wd_t0"] = simulated_water_depth

    create_histogram_with_mesh_values(gps_points_bf20, "sim_wd_t0")

    flood_scenario = BeforeOrAfterFloodScenario.bf_2020
    if flood_scenario == BeforeOrAfterFloodScenario.bf_2020:
        columns_to_lookup = ["bot_ele_t0", "wse_t0", "v_t0"]
    elif flood_scenario == BeforeOrAfterFloodScenario.af_2020:
        columns_to_lookup = ["bot_ele_end", "wse_end", "v_end"]
    else:
        raise NotImplementedError
    transect_lines_and_points = extract_specified_column_values_from_results_file(
        columns_to_lookup, mesh_with_all_results, flood_scenario
    )
    print(transect_lines_and_points)
    for i, transect_line_with_points in enumerate(transect_lines_and_points):
        if flood_scenario == BeforeOrAfterFloodScenario.bf_2020:
            plot_river_profile_from_GPS_vs_simulated_data(
                transect_line_with_points, f"out//{flood_scenario.value}_profile_{i}.html", "wse_t0", "bot_ele_t0"
            )
        elif flood_scenario == BeforeOrAfterFloodScenario.af_2020:
            plot_river_profile_from_GPS_vs_simulated_data(
                transect_line_with_points, f"out//{flood_scenario.value}_profile_{i}.html", "wse_end", "bot_ele_end"
            )





def create_summarising_mesh_with_all_results(bottom_elevation, flow_velocity, hydraulic_state):
    hydraulic_state_t_0 = "0000000-Va"
    bottom_elevation_t_0 = "0000000-Bo"
    hydraulic_state_t_end = "0000003-Va"
    bottom_elevation_t_end = "0000003-Bo"
    flow_velocity_t_0 = "0-Value"
    flow_velocity_t_end = "3-Value"
    mesh_with_all_results = gpd.GeoDataFrame(geometry=bottom_elevation.geometry, crs=2056)
    mesh_with_all_results["area"] = mesh_with_all_results.area
    mesh_with_all_results["wd_t0"] = hydraulic_state[hydraulic_state_t_0] - bottom_elevation[bottom_elevation_t_0]
    mesh_with_all_results["wd_t_end"] = (
            hydraulic_state[hydraulic_state_t_end] - bottom_elevation[bottom_elevation_t_end]
    )
    mesh_with_all_results["delta_z"] = bottom_elevation[bottom_elevation_t_end] - bottom_elevation[bottom_elevation_t_0]
    mesh_with_all_results["v_t0"] = flow_velocity[flow_velocity_t_0]
    mesh_with_all_results["v_end"] = flow_velocity[flow_velocity_t_end]
    mesh_with_all_results["bot_ele_t0"] = bottom_elevation[bottom_elevation_t_end]
    mesh_with_all_results["bot_ele_end"] = bottom_elevation[bottom_elevation_t_end]
    mesh_with_all_results["wse_t0"] = hydraulic_state[hydraulic_state_t_0]
    mesh_with_all_results["wse_end"] = hydraulic_state[hydraulic_state_t_end]
    return mesh_with_all_results


def extract_specified_column_values_from_results_file(
    columns_to_lookup: Iterable[str], mesh_with_all_results: gpd.GeoDataFrame, scenario: BeforeOrAfterFloodScenario
) -> list[OrderedProjectedGpsPointsPerProfileLine]:
    line_and_points_with_data = []
    for file_name in glob.glob(f"..\\river_profiles_from_bathymetry\\points_with_line*{scenario.value}*"):
        with open(file_name, "rb") as dump_file:
            points_with_line: OrderedProjectedGpsPointsPerProfileLine = pickle.load(dump_file)
            column_values = [[] for _ in columns_to_lookup]
            for index, point in enumerate(points_with_line.projected_gps_points.geometry):
                _contains = mesh_with_all_results.contains(point)
                if not any(_contains):
                    for column_index, _ in enumerate(columns_to_lookup):
                        column_values[column_index].append(np.nan)
                else:
                    for column_index, column_name in enumerate(columns_to_lookup):
                        value = mesh_with_all_results.loc[_contains, column_name].values[0]
                        column_values[column_index].append(value)
            for column_values, column_name in zip(column_values, columns_to_lookup):
                points_with_line.projected_gps_points[column_name] = column_values
        line_and_points_with_data.append(points_with_line)

    return line_and_points_with_data


def create_histogram_with_mesh_values(gps_points, value_to_make_histogram_from: str):
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=gps_points[value_to_make_histogram_from],
        )
    )
    fig.update_layout(
        xaxis=dict(title=f"{value_to_make_histogram_from}"),
        yaxis=dict(title="n"),
    )
    fig.to_html(f"out\\histogram_{value_to_make_histogram_from}.html")


def plot_river_profile_from_GPS_vs_simulated_data(
    ordered_gps_points_on_profile_line, filename: str, column_name_for_water_surface_elevation: str,
        column_name_for_bottom_elevation: str):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points[column_name_for_water_surface_elevation].values,

            name="simulated water surface elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points[column_name_for_bottom_elevation].values,
            name="simulated bottom elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points["H"].values,
            name="GPS bottom elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points["WSE__m_"].values,
            name="GPS WSE",
            mode="lines+markers",
        )
    )

    figure.update_xaxes(
        range=[0, 25]
        )
    figure.update_yaxes(
        range=[574.7, 577.0]
        )

    figure.write_html(filename)


# copy attributes

# calculate water depth


if __name__ == "__main__":
    main()
