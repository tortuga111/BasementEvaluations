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


def main():
    path_to_csv_3d_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\.logs\log_three_d_statistics_BeforeOrAfterFloodScenario.af_2020.csv"
    three_dimensional_results = pd.read_csv(path_to_csv_3d_results, sep=";")

    fig = px.box(three_dimensional_results, x="experiment_id", y="eroded_volume_per_area_abs_error")
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default
    fig.show()

    print(three_dimensional_results.head())


    print(gof.rmse(three_dimensional_results["eroded_volume_per_area_sim"].groupby("experiment_id"), three_dimensional_results["eroded_volume_per_area_obs"].groupby("experiment_id")))

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
