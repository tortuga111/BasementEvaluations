import geopandas as gpd
import numpy as np
from plotly import graph_objs as go


def calculate_new_field_with_absolute_deviation_to_original_point(path_to_points: str, TIN_nr: str) -> gpd.GeoDataFrame:
    points_to_evaluate: gpd.GeoDataFrame = gpd.read_file(path_to_points)

    points_to_evaluate[f"z_{TIN_nr}-WSE__m_"] = points_to_evaluate[f"z_{TIN_nr}"] - points_to_evaluate["WSE__m_"]
    rmse = np.sqrt(((points_to_evaluate[f"z_{TIN_nr}-WSE__m_"]) ** 2).mean())
    print(f"absolute mean error for GPS to {TIN_nr} {round(rmse, 2)}")

    return points_to_evaluate


def do_histogram_with_absolute_deviation(points_to_evaluate: gpd.GeoDataFrame, TIN_nr: str) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Histogram(x=points_to_evaluate[f"z_{TIN_nr}-WSE__m_"]))
    fig.update_layout(
        xaxis=dict(title=f"difference between GPS and {TIN_nr} [m]"),
        yaxis=dict(title="count"),
    )
    return fig


def do_barplot_with_absolute_deviation(points_to_evaluate: gpd.GeoDataFrame, TIN_nr: str) -> go.Figure:
    fig = go.Figure()
    x = points_to_evaluate.index
    fig.add_trace(
        go.Bar(
            x=x,
            y=points_to_evaluate[f"z_{TIN_nr}-WSE__m_"],
            name="test",
        )
    )

    fig.update_layout(
        xaxis=dict(title="index"),
        yaxis=dict(title="difference in [m]"),
    )
    return fig


def do_scatter_with_elevation_tin_vs_elevation_gps(points_to_evaluate, TIN_nr: str):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=points_to_evaluate["WSE__m_"].values,
            y=points_to_evaluate[f"z_{TIN_nr}"].values,
            name=f"WSE__m_ vs z_{TIN_nr}",
            mode="markers",
        )
    )
    figure.update_layout(
        xaxis=dict(title="elevation GPS points [m]"),
        yaxis=dict(title=f"elevation {TIN_nr} points [m]"),
    )
    figure.write_html(f"evaluation_tins\\SCATTER_plot_z_GPS_z_{TIN_nr}_difference.html")


def main():
    TIN_nr = "TIN16"
    elevation_points_to_compare = (
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\BF2020\\GPS_transects_BF2020.shp"
    )
    elevation_points_to_compare_with_abs_deviation = calculate_new_field_with_absolute_deviation_to_original_point(
        elevation_points_to_compare, TIN_nr
    )

    do_scatter_with_elevation_tin_vs_elevation_gps(elevation_points_to_compare_with_abs_deviation, TIN_nr)
    do_histogram_with_absolute_deviation(elevation_points_to_compare_with_abs_deviation, TIN_nr).write_html(
        f"evaluation_tins\\histogram_z_GPS_z_{TIN_nr}_difference.html"
    )
    do_barplot_with_absolute_deviation(elevation_points_to_compare_with_abs_deviation, TIN_nr).write_html(
        f"evaluation_tins\\barplot_z_GPS_z_{TIN_nr}_difference.html"
    )


if __name__ == "__main__":
    main()
