import glob
import os.path
import pickle
from dataclasses import replace
from typing import Iterable

import geopandas as gpd
from plotly import graph_objs as go
from plotly.subplots import make_subplots

from extract_data.summarising_mesh import assign_requested_values_from_summarising_mesh_to_point
from profile_creation.containers import BeforeOrAfterFloodScenario, OrderedProjectedGpsPointsPerProfileLine


def evaluate_points_along_profiles(
    mesh_with_all_results: gpd.GeoDataFrame,
    flood_scenario: BeforeOrAfterFloodScenario,
    path_to_folder_containing_points_with_line: str,
    columns_to_lookup: list,
    experiment_id: str,
) -> None:
    transect_lines_and_points = extract_specified_column_values_from_results_file(
        columns_to_lookup, mesh_with_all_results, flood_scenario, path_to_folder_containing_points_with_line
    )
    for i, transect_line_with_points in enumerate(transect_lines_and_points):
        plot_river_profile_from_gps_vs_simulated_data(
            transect_line_with_points.projected_gps_points,
            f"out\\{flood_scenario.value}_{experiment_id}_id_profile_{i}.html",
        )


def extract_specified_column_values_from_results_file(
    columns_to_lookup: Iterable[str],
    mesh_with_all_results: gpd.GeoDataFrame,
    flood_scenario: BeforeOrAfterFloodScenario,
    path_to_folder_containing_points_with_line: str,
) -> list[OrderedProjectedGpsPointsPerProfileLine]:
    updated_line_and_points_with_data = []
    for file_name in glob.glob(
        os.path.join(path_to_folder_containing_points_with_line, f"points_with_line*{flood_scenario.value}*")
    ):
        with open(file_name, "rb") as dump_file:
            points_with_line: OrderedProjectedGpsPointsPerProfileLine = pickle.load(dump_file)
            updated_points = assign_requested_values_from_summarising_mesh_to_point(
                columns_to_lookup, mesh_with_all_results, points_with_line.projected_gps_points
            )
            updated_line_and_points_with_data.append(replace(points_with_line, projected_gps_points=updated_points))
    return updated_line_and_points_with_data


def create_histogram_with_mesh_values(
    gps_points: gpd.GeoDataFrame, column_to_make_histogram_from: str, flood_scenario: BeforeOrAfterFloodScenario, experiment_id: str
):
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=gps_points[column_to_make_histogram_from]))
    fig.update_layout(
        xaxis=dict(title=f"{column_to_make_histogram_from}"),
        yaxis=dict(title="n"),
    )
    fig.write_html(f"out\\histogram_{column_to_make_histogram_from}_{flood_scenario}_{experiment_id}.html")


def plot_river_profile_from_gps_vs_simulated_data(
    ordered_gps_points_on_profile_line: gpd.GeoDataFrame,
    filename: str,
):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line["distance"].values,
            y=ordered_gps_points_on_profile_line["wse"].values,
            name="simulated water surface elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line["distance"].values,
            y=ordered_gps_points_on_profile_line["bot_ele"].values,
            name="simulated bottom elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line["distance"].values,
            y=ordered_gps_points_on_profile_line["H"].values,
            name="GPS bottom elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line["distance"].values,
            y=ordered_gps_points_on_profile_line["WSE__m_"].values,
            name="GPS WSE",
            mode="lines+markers",
        )
    )

    figure.update_xaxes(range=[0, 25])
    figure.update_yaxes(range=[ordered_gps_points_on_profile_line["H"].values.min()-0.5, (ordered_gps_points_on_profile_line["WSE__m_"].values.max())+0.5])

    figure.write_html(filename)
    return figure
