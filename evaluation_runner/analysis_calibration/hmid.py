import os
import pathlib
import pickle

import geopandas as gpd
import numpy as np
import pandas as pd
from plotly import graph_objects as go
import plotly.express as px

from misc.dataclasses_for_evaluations import ColumnNamePair


def create_scatter_plot(hmid_results):
    indices = hmid_results.groupby("experiment_id")["time_step"].transform(max) == hmid_results["time_step"]
    isolated = hmid_results[indices]
    isolated.to_csv("hmid.csv")

    path_to_csv_hmid_summary = (
        r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\out\HMID\summary_hmid.csv"
    )
    hmid_summary = pd.read_csv(path_to_csv_hmid_summary, sep=",")

    fig = px.scatter(
        hmid_summary,
        x="Q",
        y="water_depth_variability",
        color="length",
    )
    fig.update_layout(
        xaxis=dict(title="maximum discharge [m\u00b3/s]", range=[1, None]),
        yaxis=dict(title="water depth variability [%]"),
    )
    fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
        font=dict(
            size=12,
        ),
        showlegend=True,
    )
    fig.write_image(
        "scatter_waterdepthvari.svg",
        format="svg",
        width=1500,
        height=1000,
        scale=2,
    )

    fig.show()

    fig = px.scatter(
        hmid_summary,
        x="Q",
        y="flow_velocity_variability",
        color="length",
    )
    fig.update_layout(
        xaxis=dict(title="maximum discharge [m\u00b3/s]", range=[1, None]),
        yaxis=dict(title="flow velocity variability [%]"),
    )
    fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
        font=dict(
            size=12,
        ),
        showlegend=True,
    )
    fig.write_image(
        "scatter_flowvelocity.svg",
        format="svg",
        width=1500,
        height=1000,
        scale=2,
    )

    fig.show()

    fig = px.scatter(hmid_summary, x="Q", y="hydro_morphological_index_of_diversity", color="length")

    fig.update_layout(
        xaxis=dict(title="maximum discharge [m\u00b3/s]", range=[1, None]),
        yaxis=dict(title="HMID"),
    )
    fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
        font=dict(
            size=12,
        ),
        showlegend=True,
    )
    fig.write_image(
        "scatter_hmid.svg",
        format="svg",
        width=1500,
        height=1000,
        scale=2,
    )

    fig.show()

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=hmid_summary["Q"],
            y=hmid_summary["water_depth_variability"],
            mode="markers",
            name="water_depth_variability",
            hoverinfo="name",
        )
    )

    fig.update_layout(legend=dict(yanchor="bottom", y=0.01, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
        font=dict(
            size=20,
        ),
        showlegend=True,
    )
    fig.show()


# fig.update_layout(legend=go.layout.Legend(yanchor="top", xanchor="left",
# x=1, y=1
#                              ))
# fig.write_image("scatter_hmid.svg", format="svg", width=1500, height=1000, scale=2,)
# fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default


def main():
    path_to_csv_hmid_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\out\HMID\log_hmid_input_01_fine_mesh.csv"
    hmid_results = pd.read_csv(path_to_csv_hmid_results, sep=";")

    create_scatter_plot(hmid_results)


if __name__ == "__main__":
    main()
