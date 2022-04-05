from typing import Iterable, Optional

import geopandas as gpd
from matplotlib import pyplot as plt
from plotly import graph_objs as go

from water_surface_preparation.data_classes.points_per_line import TransectLinesAtPoint, ProcessedPointsPerCenterLine


def debug_plot(geo_data_frame: gpd.GeoDataFrame, filename: str) -> None:
    geo_data_frame.plot()
    plt.savefig(f"out\\{filename}.jpg")


def create_plot_for_transect_lines(transect_lines_and_points: Iterable[TransectLinesAtPoint], i: int) -> None:
    all_lines = [element.right_line for element in transect_lines_and_points] + [
        element.left_line for element in transect_lines_and_points
    ]
    data_frame_with_all_lines = gpd.GeoDataFrame(geometry=all_lines)
    debug_plot(data_frame_with_all_lines, f"transect_lines_and_points{i}")


def plot_smooth_vs_raster_elevation(
    i: int,
    processed_center_points: gpd.GeoDataFrame,
    interpolated_points_along_center_line_with_center_line: ProcessedPointsPerCenterLine,
    interpolated_points_along_center_line_with_dsm_value: gpd.GeoDataFrame,
    gps_points_along_center_line: Optional[gpd.GeoDataFrame],
):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=processed_center_points.projected_points["distance"].values,
            y=processed_center_points.projected_points["z_smooth"].values,
            name="distance vs z_smooth",
            mode="markers",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=processed_center_points.projected_points["distance"].values,
            y=processed_center_points.projected_points["z_raster"].values,
            name="distance vs z_raster",
            mode="markers",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=interpolated_points_along_center_line_with_center_line.projected_points["distance"].values,
            y=interpolated_points_along_center_line_with_center_line.projected_points["z_interpolated"].values,
            name="distance vs z_interpolated",
            mode="markers",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=interpolated_points_along_center_line_with_dsm_value["distance"].values,
            y=interpolated_points_along_center_line_with_dsm_value["z_raster"].values,
            name="distance vs elevation_dsm",
            mode="markers",
        )
    )

    if gps_points_along_center_line is not None:
        figure.add_trace(
            go.Scatter(
                x=gps_points_along_center_line["distance"].values,
                y=gps_points_along_center_line["z_raster"].values,
                name="distance_vs_gps",
                mode="markers",
            )
        )
    figure.update_layout(xaxis={"title": "distance"}, yaxis={"title": "elevation"})
    figure.write_html(f"out\\_plot_smooth_vs_raster_elevation{i}.html")


def plot_interpolated_vs_smooth_and_raster_elevation(
    i, interpolated_points_along_center_line_with_center_line, processed_center_points
):
    plt.show(block=False)
    plt.scatter(
        x=processed_center_points.projected_points["distance"].values,
        y=processed_center_points.projected_points["z_smooth"].values,
        c="orange",
    )
    plt.scatter(
        x=processed_center_points.projected_points["distance"].values,
        y=processed_center_points.projected_points["z_raster"].values,
        c="red",
    )
    plt.scatter(
        x=interpolated_points_along_center_line_with_center_line.projected_points["distance"],
        y=interpolated_points_along_center_line_with_center_line.projected_points["z_interpolated"].values,
        c="green",
    )
    plt.savefig(f"out\\interpolated_vs_smooth_and_raster{i}.jpg")
