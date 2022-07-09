import glob
import os.path
import pickle
from copy import deepcopy
from dataclasses import replace
from typing import Iterable

import geopandas as gpd
from plotly import graph_objs as go
import plotly.express as px

from extract_data.summarising_mesh import (
    assign_requested_values_from_summarising_mesh_to_point,
    StateToNameInShapeFileMapping,
)
from profile_creation.containers import BeforeOrAfterFloodScenario, OrderedProjectedGpsPointsPerProfileLine


def evaluate_points_along_profiles(
    mesh_with_all_results: gpd.GeoDataFrame,
    flood_scenario: BeforeOrAfterFloodScenario,
    path_to_folder_containing_points_with_line: str,
    colum_name_mapping: StateToNameInShapeFileMapping,
    experiment_id: str,
) -> None:
    transect_lines_and_points = extract_specified_column_values_from_results_file(
        [pair.final_name for pair in colum_name_mapping],
        mesh_with_all_results,
        flood_scenario,
        path_to_folder_containing_points_with_line,
    )
    file_path = f"out\\profiles\\{flood_scenario.value}_{experiment_id}\\"
    if not os.path.exists(file_path):
        os.mkdir(file_path)
    for i, transect_line_with_points in enumerate(transect_lines_and_points):
        file_name = f"profile_{i}"
        figure = plot_river_profile_from_gps_vs_simulated_data(
            transect_line_with_points.projected_gps_points, file_path + file_name + ".html", colum_name_mapping
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


def create_scatter_plot(
    gps_points: gpd.GeoDataFrame,
    column_to_make_scatter_from_sim: str,
    flood_scenario: BeforeOrAfterFloodScenario,
    experiment_id: str,
    column_to_make_scatter_from_obs: str,
):
    file_path = f"out\\scatter_plots_{flood_scenario.value}\\{experiment_id}\\"
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_name = f"scatter_{column_to_make_scatter_from_sim}.html"
    figure = px.scatter(
        gps_points,
        x=gps_points[column_to_make_scatter_from_obs].values,
        y=gps_points[column_to_make_scatter_from_sim].values,
        trendline="ols",
    )
    scatter_points, trend_line = tuple(figure.select_traces())
    fig = go.Figure()
    trend_line: go.Trace
    trend_line.update(name="linear regression", showlegend=True)
    fig.add_trace(trend_line)
    osbervation_points = go.Scatter(
        x=gps_points[column_to_make_scatter_from_obs].values,
        y=gps_points[column_to_make_scatter_from_sim].values,
        name="simulated vs observed water depths",
        mode="markers",
    )
    fig.add_trace(osbervation_points)
    max_value = max(
        gps_points[column_to_make_scatter_from_obs].max(), gps_points[column_to_make_scatter_from_sim].max()
    )
    ideal_line = go.Scatter(x=[0, max_value], y=[0, max_value], line=dict(dash="dash"), showlegend=False)
    fig.add_trace(ideal_line)
    fig.update_layout(
        xaxis=dict(title="observed water depth [m]"),
        yaxis=dict(title="simulated water depth [m]"),
        font=dict(
            size=20,
        ),
    )
    fig.write_html(file_path + file_name)

    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
    )
    fig.update_xaxes(range=[0, 1.2])
    fig.update_yaxes(range=[0, 1.2])
    fig.update_layout(legend=dict(yanchor="top", xanchor="left", x=0.01, y=0.99))
    png_filename = file_name if file_name.endswith(".png") else f"{file_name}.png"
    fig.write_image(
        file_path + png_filename,
        format="png",
        width=600,
        height=600,
        scale=2,
    )


def create_scatter_plot_for_velocities(
    gps_points: gpd.GeoDataFrame,
    column_to_make_scatter_from_sim: str,
    flood_scenario: BeforeOrAfterFloodScenario,
    experiment_id: str,
    column_to_make_scatter_from_obs: str,
):
    file_path = f"out\\scatter_plots_{flood_scenario.value}\\{experiment_id}_velocity\\"
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_name = f"scatter_{column_to_make_scatter_from_sim}.html"
    figure = px.scatter(
        gps_points,
        x=gps_points[column_to_make_scatter_from_obs].values,
        y=gps_points[column_to_make_scatter_from_sim].values,
        trendline="ols",
    )
    scatter_points, trend_line = tuple(figure.select_traces())
    fig = go.Figure()
    trend_line: go.Trace
    trend_line.update(name="linear regression", showlegend=True)
    fig.add_trace(trend_line)
    osbervation_points = go.Scatter(
        x=gps_points[column_to_make_scatter_from_obs].values,
        y=gps_points[column_to_make_scatter_from_sim].values,
        name="simulated vs observed flow velocities",
        mode="markers",
    )
    fig.add_trace(osbervation_points)
    max_value = max(
        gps_points[column_to_make_scatter_from_obs].max(), gps_points[column_to_make_scatter_from_sim].max()
    )
    ideal_line = go.Scatter(x=[0, max_value], y=[0, max_value], line=dict(dash="dash"), showlegend=False)
    fig.add_trace(ideal_line)
    fig.update_layout(
        xaxis=dict(title="observed flow velocity [m/s]"),
        yaxis=dict(title="simulated flow velocity [m/s]"),
        font=dict(
            size=20,
        ),
    )
    fig.write_html(file_path + file_name)

    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
    )
    fig.update_xaxes(range=[0, 1.2])
    fig.update_yaxes(range=[0, 1.2])
    fig.update_layout(legend=dict(yanchor="top", xanchor="left", x=0.01, y=0.99))
    png_filename = file_name if file_name.endswith(".png") else f"{file_name}.png"
    fig.write_image(
        file_path + png_filename,
        format="png",
        width=600,
        height=600,
        scale=2,
    )


def plot_river_profile_from_gps_vs_simulated_data(
    ordered_gps_points_on_profile_line: gpd.GeoDataFrame,
    filename: str,
    state_to_name_in_shape_file_mapping: StateToNameInShapeFileMapping,
):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line["distance"].values,
            y=ordered_gps_points_on_profile_line[state_to_name_in_shape_file_mapping.water_depth.final_name].values
            + ordered_gps_points_on_profile_line[
                state_to_name_in_shape_file_mapping.bottom_elevation.final_name
            ].values,
            name="simulated water surface elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line["distance"].values,
            y=ordered_gps_points_on_profile_line[
                state_to_name_in_shape_file_mapping.bottom_elevation.final_name
            ].values,
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
            (
                ordered_gps_points_on_profile_line[
                    state_to_name_in_shape_file_mapping.water_depth.final_name
                ].values.max()
            )
            + 0.5,
        ]
    )

    figure.write_html(filename)
    return figure


def format_and_save_profile_as_png(figure: go.Figure, filename: str) -> None:
    formatted_figure = figure

    formatted_figure.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
    )
    formatted_figure.update_xaxes(range=[0, 25])
    formatted_figure.update_yaxes(range=[574.5, 577.5])
    formatted_figure.update_layout(showlegend=True)
    png_filename = filename if filename.endswith(".png") else f"{filename}.png"
    formatted_figure.write_image(
        png_filename,
        format="png",
        width=600,
        height=750,
        scale=2,
    )
