import os

import geopandas as gpd
import plotly.graph_objects as go
from geopandas import GeoDataFrame


def calculate_new_field_with_absolute_deviation_to_original_point(path_to_points: str) -> GeoDataFrame:
    points_to_evaluate: gpd.GeoDataFrame = gpd.read_file(path_to_points)

    points_to_evaluate["BF20noGCP-abs_z"] = (points_to_evaluate["z_BF20_no"] - (points_to_evaluate["z_GPS"]) ** 2) ** (
        1 / 2
    )
    print(f"absolute mean error for z_BF20_no {round(points_to_evaluate['BF20noGCP-abs_z'].mean(), 2)}")

    points_to_evaluate["AF20noGCP-abs_z"] = ((points_to_evaluate["z_AF20_no"] - points_to_evaluate["z_GPS"]) ** 2) ** (
        1 / 2
    )
    print(f"absolute mean error for z_AF20_no {round(points_to_evaluate['AF20noGCP-abs_z'].mean(), 2)}")

    points_to_evaluate["AF20-abs_z"] = ((points_to_evaluate["z_AF20"] - points_to_evaluate["z_GPS"]) ** 2) ** (1 / 2)
    print(f"absolute mean error for z_AF20 {round(points_to_evaluate['AF20-abs_z'].mean(), 2)}")

    points_to_evaluate["AF20_cor-abs_z"] = ((points_to_evaluate["z_AF20_cor"] - points_to_evaluate["z_GPS"]) ** 2) ** (
        1 / 2
    )
    print(f"absolute mean error for AF20_cor {round(points_to_evaluate['AF20_cor-abs_z'].mean(), 2)}")

    points_to_evaluate["AF20_20-abs_z"] = ((points_to_evaluate["z_AF20_20"] - points_to_evaluate["z_GPS"]) ** 2) ** (
        1 / 2
    )
    print(f"absolute mean error for AF20_20 {round(points_to_evaluate['AF20_20-abs_z'].mean(), 2)}")

    points_to_evaluate["BF20-abs_z"] = ((points_to_evaluate["z_BF20"] - points_to_evaluate["z_GPS"]) ** 2) ** (1 / 2)
    print(f"absolute mean error for z_BF20 {round(points_to_evaluate['BF20-abs_z'].mean(), 2)}")

    points_to_evaluate["BF20_cor-abs_z"] = ((points_to_evaluate["z_BF20_cor"] - points_to_evaluate["z_GPS"]) ** 2) ** (
        1 / 2
    )
    print(f"absolute mean error for z_BF20_cor {round(points_to_evaluate['BF20_cor-abs_z'].mean(), 2)}")

    points_to_evaluate["AF21-abs_z"] = ((points_to_evaluate["z_AF21"] - points_to_evaluate["z_GPS"]) ** 2) ** (1 / 2)
    print(f"absolute mean error for z_AF21 {round(points_to_evaluate['AF21-abs_z'].mean(), 2)}")

    return points_to_evaluate


def calculate_new_field_with_deviation_to_original_point(path_to_points: str) -> GeoDataFrame:
    points_with_difference_to_dsm: gpd.GeoDataFrame = gpd.read_file(path_to_points)

    points_with_difference_to_dsm["z_BF20_noGCP-z_GPS"] = (
        points_with_difference_to_dsm["z_BF20_no"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_BF20_no {round(points_with_difference_to_dsm['z_BF20_noGCP-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_AF20_noGCP-z_GPS"] = (
        points_with_difference_to_dsm["z_AF20_no"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_AF20_no {round(points_with_difference_to_dsm['z_AF20_noGCP-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_AF20-z_GPS"] = (
        points_with_difference_to_dsm["z_AF20"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_AF20 {round(points_with_difference_to_dsm['z_AF20-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_AF20_cor-z_GPS"] = (
        points_with_difference_to_dsm["z_AF20_cor"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_AF20_cor {round(points_with_difference_to_dsm['z_AF20_cor-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_AF20_20-z_GPS"] = (
        points_with_difference_to_dsm["z_AF20_20"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_AF20_20 {round(points_with_difference_to_dsm['z_AF20_20-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_BF20-z_GPS"] = (
        points_with_difference_to_dsm["z_BF20"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_BF20 {round(points_with_difference_to_dsm['z_BF20-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_BF20_cor-z_GPS"] = (
        points_with_difference_to_dsm["z_BF20_cor"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_BF20_cor {round(points_with_difference_to_dsm['z_BF20_cor-z_GPS'].mean(), 2)}")

    points_with_difference_to_dsm["z_AF21-z_GPS"] = (
        points_with_difference_to_dsm["z_AF21"] - points_with_difference_to_dsm["z_GPS"]
    )
    print(f"mean error for z_AF21 {round(points_with_difference_to_dsm['z_AF21-z_GPS'].mean(), 2)}")

    return points_with_difference_to_dsm


def do_histogram_with_absolute_deviation(points: GeoDataFrame) -> go.Figure:
    fig = go.Figure()
    x = points["ID"]
    names = [
        "BF20noGCP-abs_z",
        "AF20noGCP-abs_z",
        "AF20-abs_z",
        "AF20_cor-abs_z",
        "AF20_20-abs_z",
        "BF20-abs_z",
        "AF21-abs_z",
        "BF20_cor-abs_z",
    ]
    for name in names:
        fig.add_trace(
            go.Bar(
                x=x,
                y=points[name],
                name=name,
            )
        )

    fig.update_layout(
        xaxis=dict(title="GPS z"),
        yaxis=dict(title="m"),
    )
    return fig


def do_histogram_with_deviation(points: GeoDataFrame) -> go.Figure:
    fig = go.Figure()
    x = points["ID"]
    names = [
        "z_BF20_noGCP-z_GPS",
        "z_AF20_noGCP-z_GPS",
        "z_AF20-z_GPS",
        "z_AF20_cor-z_GPS",
        "z_AF20_20-z_GPS",
        "z_BF20-z_GPS",
        "z_BF20_cor-z_GPS",
        "z_AF21-z_GPS",
    ]
    for name in names:
        fig.add_trace(
            go.Bar(
                x=x,
                y=points[name],
                name=name,
            )
        )

    fig.update_layout(
        xaxis=dict(title="GPS points"),
        yaxis=dict(title="difference in m"),
    )
    return fig


def main() -> None:
    path_to_points: str = os.path.join(
        os.getcwd(), "..\\..\\..\\..\\02_Data\\02_prep_bathy\\00_gcp_prep\\gcp_elev_all_dsm13.shp"
    )

    absolute_points = calculate_new_field_with_absolute_deviation_to_original_point(path_to_points)
    points_difference = calculate_new_field_with_deviation_to_original_point(path_to_points)

    do_histogram_with_absolute_deviation(absolute_points).write_html("absolute_deviation_barplot.html")

    do_histogram_with_deviation(points_difference).write_html("deviation_barplot.html")


if __name__ == "__main__":
    main()
