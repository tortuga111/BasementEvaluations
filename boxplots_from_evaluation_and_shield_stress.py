import math
from typing import Iterable, Dict

import wget
import rasterio as rio
from rasterio import mask

import matplotlib.pyplot as plt

import numpy as np
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import goodness_of_fit as gof

import folium

from misc.dataclasses_for_evaluations import ColumnNamePair
from statistical_formulas.formulas_goodness_of_fit import calculate_root_mean_square_error, calculate_index_of_agreement


def calculate_index_of_agreement_for_volumes(simulated_deposited, observed_deposited):
    return 1 - np.divide(
        sum(np.square(np.subtract(simulated_deposited, observed_deposited))),
        sum(
            np.square(
                abs(np.subtract(simulated_deposited, np.mean(observed_deposited)))
                + abs(np.subtract(observed_deposited, np.mean(observed_deposited))),
            )
        ),
    )


def main():
    path_to_csv_3d_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\.logs\log_three_d_statistics_BeforeOrAfterFloodScenario.af_2020.csv"
    three_dimensional_results = pd.read_csv(path_to_csv_3d_results, sep=";")

    fig = go.Figure()
    group_nr = 0
    for group_name, group in three_dimensional_results.groupby("experiment_id"):
        group_nr += 1
        fig.add_trace(
            go.Box(
                x=[group_nr - 0.25] * len(group),
                y=group["eroded_volume_per_area_abs_error"],
                name=group_name,
                marker_color="indianred",
            )
        )
        fig.add_trace(
            go.Box(
                x=[group_nr + 0.25] * len(group),
                y=group["deposited_volume_per_area_abs_error"],
                name=group_name,
                marker_color="lightseagreen",
            )
        )
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default
    fig.show()

    # calculate goodness of fit parameters for volumes:
    for group_name, group in three_dimensional_results.groupby("experiment_id"):

        column_names_deposited_volume_change_per_area = ColumnNamePair(
            observed=group["deposited_volume_per_area_dod"], simulated=group["deposited_volume_per_area_sim"]
        )

        experiment_id = group["experiment_id"]
        observed_deposited = group["deposited_volume_per_area_dod"]
        simulated_deposited = group["deposited_volume_per_area_sim"]

        observed_eroded = group["eroded_volume_per_area_dod"]
        simulated_eroded = group["eroded_volume_per_area_sim"]

        index_of_agreement_deposited_volume = calculate_index_of_agreement_for_volumes(
            observed_deposited, simulated_deposited
        )

        root_mean_square_error_deposition = sum(np.square(simulated_deposited - observed_deposited))
        root_mean_square_error_erosion = sum(np.square(simulated_eroded - observed_eroded))

        print("root mean square error deposition = ", root_mean_square_error_deposition)
        print("root mean square error erosion = ", root_mean_square_error_erosion)
        print(f"index_of_agreement for deposited volume =", index_of_agreement_deposited_volume)

        index_of_agreement_eroded_volume = calculate_index_of_agreement_for_volumes(observed_eroded, simulated_eroded)
        print(f"index_of_agreement for eroded volume =", index_of_agreement_eroded_volume)

    if stop := False:
        return

    path_to_csv_shear_stress_results = (
        r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\.logs\log_shear_stress.csv"
    )
    shear_stress_results = pd.read_csv(path_to_csv_shear_stress_results, sep=";")

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["area_guenter_criterion"],
            mode="lines+markers",
            name="area where guenter criterion is reached",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_critical_shield_stress"],
            mode="lines+markers",
            name="area where critical shield stress is reached",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["area_guenter_criterion_chezy"],
            mode="lines+markers",
            name="area where guenter criterion is reached with chezy",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_critical_shield_stress_chezy"],
            mode="lines+markers",
            name="area where critical shield stress is reached with chezy",
        )
    )
    fig.update_layout(
        xaxis=dict(title=r"discharge $[\frac{$m^{3}$}{s}$"),
        yaxis=dict(title="area [m^2^]"),
        font=dict(
            size=12,
        ),
    )
    fig.show()


if __name__ == "__main__":
    main()
