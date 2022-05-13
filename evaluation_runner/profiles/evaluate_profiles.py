import glob
import os.path
import pickle
from copy import deepcopy
from dataclasses import replace
from typing import Iterable

import geopandas as gpd
from plotly import graph_objs as go

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
    file_path = f"out\\profiles\\{flood_scenario.value}_{experiment_id}\\"
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    for i, transect_line_with_points in enumerate(transect_lines_and_points):
        file_name = f"profile_{i}"
        figure = plot_river_profile_from_gps_vs_simulated_data(
            transect_line_with_points.projected_gps_points, file_path + file_name + ".html"
        )
        format_and_save_profile_as_png(figure, file_path + file_name + ".png")


def extract_specified_column_values_from_results_file(
        columns_to_lookup: Iterable[str],
        mesh_with_all_results: gpd.GeoDataFrame,
        flood_scenario: BeforeOrAfterFloodScenario,
        path_to_folder_containing_points_with_line: str,
) -> list[OrderedProjectedGpsPointsPerProfileLine]:
    updated_line_and_points_with_data = []
    file_names = glob.glob(
        os.path.join(path_to_folder_containing_points_with_line, f"points_with_line*{flood_scenario.value}*")
    )
    for file_name in sorted(file_names):
        with open(file_name, "rb") as dump_file:
            points_with_line: OrderedProjectedGpsPointsPerProfileLine = pickle.load(dump_file)
            updated_points = assign_requested_values_from_summarising_mesh_to_point(
                columns_to_lookup, mesh_with_all_results, points_with_line.projected_gps_points
            )
            updated_line_and_points_with_data.append(replace(points_with_line, projected_gps_points=updated_points))
    return updated_line_and_points_with_data


def create_histogram_with_mesh_values(
        gps_points: gpd.GeoDataFrame,
        column_to_make_histogram_from: str,
        flood_scenario: BeforeOrAfterFloodScenario,
        experiment_id: str,
):
    file_path = f"out\\histograms\\{flood_scenario.value}_{experiment_id}\\"
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_name = f"histogram_{column_to_make_histogram_from}.html"
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=gps_points[column_to_make_histogram_from]))
    fig.update_layout(
        xaxis=dict(title=f"{column_to_make_histogram_from}"),
        yaxis=dict(title="n"),
    )
    fig.write_html(file_path + file_name)


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
    figure.update_yaxes(
        range=[
            ordered_gps_points_on_profile_line["H"].values.min() - 0.5,
            (ordered_gps_points_on_profile_line["wse"].values.max()) + 0.5,
        ]
    )

    figure.write_html(filename)
    return figure


def format_and_save_profile_as_png(figure: go.Figure, filename: str) -> None:
    formatted_figure = figure

    formatted_figure.update_layout(
        autosize=False,
        margin=dict(
            l=1,
            r=1,
            b=1,
            t=1,
            pad=4
        ),
        paper_bgcolor="LightSteelBlue",
    )
    formatted_figure.update_xaxes(range=[0, 25])
    formatted_figure.update_yaxes(range=[574.5, 577.5])
    formatted_figure.update_layout(showlegend=False)
    png_filename = filename if filename.endswith(".png") else f"{filename}.png"
    formatted_figure.write_image(png_filename, format="png", width=600, height=750, scale=2, )
