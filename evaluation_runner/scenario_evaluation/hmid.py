import os
import pathlib
import pickle

import geopandas as gpd
import numpy as np
import pandas as pd
from plotly import graph_objects as go
import plotly.express as px

from tools.figure_generator import create_figure_if_none_given
from misc.dataclasses_for_evaluations import ColumnNamePair


def create_scatter_plot(hmid_results):
    indices = hmid_results.groupby("experiment_id")["time_step"].transform(max) == hmid_results["time_step"]
    isolated = hmid_results[indices]
    isolated.to_csv("hmid.csv")

    path_to_csv_hmid_summary = (
        r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\out\HMID\hmid.csv"
    )
    hmid_summary = pd.read_csv(path_to_csv_hmid_summary, sep=",")

    fig = px.bar(
        hmid_summary,
        x="Q",
        y="water_depth_variability",
        color="length",
        barmode="group",
    )

    fig.update_layout(
        xaxis=dict(title="scenario maximum discharge [m\u00b3/s]"),
        yaxis=dict(title="water depth variability [%]", range=[70, 100]),
    )
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        font=dict(
            size=20,
        ),
        plot_bgcolor="#f2f2f2",
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

    fig = px.bar(
        hmid_summary,
        x="Q",
        y="flow_velocity_variability",
        color="length",
        barmode="group",
    )
    fig.update_layout(
        xaxis=dict(title="scenario maximum discharge [m\u00b3/s]"),
        yaxis=dict(title="flow velocity variability [%]", range=[70, 100]),
    )
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        plot_bgcolor="#f2f2f2",
        font=dict(
            size=20,
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

    fig = px.bar(hmid_summary, x="Q", y="hydro_morphological_index_of_diversity", color="length", barmode="group",
                 )

    fig.update_layout(
        xaxis=dict(title="scenario maximum discharge [m\u00b3/s]"),
        yaxis=dict(title="HMID", range=[8, 15]),
    )
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="right", x=0.99))
    fig.update_layout(
        autosize=False,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        plot_bgcolor="#f2f2f2",
        font=dict(
            size=20,
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
