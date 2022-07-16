import os
import pathlib
import pickle

import geopandas as gpd
import numpy as np
import pandas as pd
from plotly import graph_objects as go

from misc.dataclasses_for_evaluations import ColumnNamePair


def calculate_index_of_agreement_for_volumes(simulated_deposited, observed_deposited, area):
    return 1 - np.divide(
        sum(np.square(np.subtract(simulated_deposited, observed_deposited)) * area),
        sum(
            np.square(
                abs(np.subtract(simulated_deposited, np.mean(observed_deposited)) * area)
                + abs(np.subtract(observed_deposited, np.mean(observed_deposited)) * area),
            )
        ),
    )


def create_boxplot(three_dimensional_results):
    fig = go.Figure()
    group_nr = 0
    for group_name, group in three_dimensional_results.groupby("experiment_id"):
        group_nr += 1
        fig.add_trace(
            go.Box(
                x=[group_nr - 0.15] * len(group),
                # x=group["experiment_id"],
                y=group["eroded_volume_per_area_abs_error"],
                # name=str(group_name)[:13],
                name="erosion",
                marker_color="#D41159",
                hoverinfo="name",
                width=0.25,
            )
        )
        fig.add_trace(
            go.Box(
                x=[group_nr + 0.15] * len(group),
                # x=group["experiment_id"],
                y=group["deposited_volume_per_area_abs_error"],
                # name=str(group_name)[:13] + "#",
                name="deposition",
                marker_color="#1A85FF",
                hoverinfo="name",
                width=0.3,
            )
        )
    fig.update_layout(
        xaxis=dict(title="calibration scenario"),
        yaxis=dict(title="absolute error [m]", range=[-1, 1]),
    )
    fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        font=dict(
            size=20,
        ),
        plot_bgcolor="#f2f2f2",
        showlegend=False,
    )
    # fig.update_layout(legend=go.layout.Legend(yanchor="top", xanchor="left",
    # x=1, y=1
    #                              ))
    fig.write_image(
        "boxplot_3D_analysis.svg",
        format="svg",
        width=1500,
        height=1000,
        scale=2,
    )
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default
    fig.show()


def create_boxplot_for_gps_points(two_dimensional_results):
    fig = go.Figure()
    group_nr = 0
    for group_name, group in two_dimensional_results.groupby("filename"):
        group_nr += 1
        fig.add_trace(
            go.Box(
                x=[group_nr] * len(group),
                y=group["wd_sim_gps"],
                # name=str(group_name)[:13],
                name="erosion",
                marker_color="#D41159",
                hoverinfo="name",
                width=0.25,
                showlegend=False,
            )
        )

    # fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
        font=dict(
            size=30,
        ),
    )

    # fig.update_layout(legend=go.layout.Legend(yanchor="top", xanchor="left",
    # x=1, y=1
    #                              ))
    fig.write_image("boxplot_1D_analysis.svg", format="svg", width=1500, height=1000, scale=2)
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default
    fig.show()


def calculate_goodness_of_fit_parameters_for_three_dimensional(three_dimensional_results):
    for group_name, group in three_dimensional_results.groupby("experiment_id"):
        column_names_deposited_volume_change_per_area = ColumnNamePair(
            observed=group["deposited_volume_per_area_dod"], simulated=group["deposited_volume_per_area_sim"]
        )

        experiment_id = group["experiment_id"]
        observed_deposited = group["deposited_volume_per_area_dod"]
        simulated_deposited = group["deposited_volume_per_area_sim"]

        observed_eroded = group["eroded_volume_per_area_dod"]
        simulated_eroded = group["eroded_volume_per_area_sim"]
        area = group["area_polygon"]

        index_of_agreement_deposited_volume = calculate_index_of_agreement_for_volumes(
            observed_deposited, simulated_deposited, area
        )

        root_mean_square_error_deposition = sum(np.square(simulated_deposited - observed_deposited) * area) / sum(area)
        root_mean_square_error_erosion = sum(np.square(simulated_eroded - observed_eroded) * area) / sum(area)

        print("root mean square error deposition of ", group_name, "=", root_mean_square_error_deposition)
        print("root mean square error erosion", group_name, "=", root_mean_square_error_erosion)
        print(f"index_of_agreement for deposited volume", group_name, "=", index_of_agreement_deposited_volume)

        index_of_agreement_eroded_volume = calculate_index_of_agreement_for_volumes(
            observed_eroded, simulated_eroded, area
        )
        print(f"index_of_agreement for eroded volume", group_name, "=", index_of_agreement_eroded_volume)


def main():
    path_to_csv_3d_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\.logs\log_three_d_statistics_BeforeOrAfterFloodScenario.af_2020.csv"
    three_dimensional_results = pd.read_csv(path_to_csv_3d_results, sep=";")

    create_boxplot(three_dimensional_results)

    # calculate goodness of fit parameters for volumes:
    calculate_goodness_of_fit_parameters_for_three_dimensional(three_dimensional_results)

    all_dataframes = []
    directory = "out\\gps_points_calibration"
    for filepath in pathlib.Path(directory).glob("**/*"):
        with open(filepath, "rb") as pickled:
            gps_points: gpd.GeoDataFrame = pickle.load(pickled)
            gps_points["filename"] = filepath.name
            all_dataframes.append(gps_points)

    #combined = pd.concat(all_dataframes, axis=0).reset_index(drop=True)

    #create_boxplot_for_gps_points(combined)


if __name__ == "__main__":
    main()
