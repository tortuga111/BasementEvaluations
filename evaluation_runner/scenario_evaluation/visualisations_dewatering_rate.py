import os
from typing import Optional

import pandas as pd
from geopandas import GeoDataFrame
from plotly import graph_objects as go
import plotly.express as px
from tools.figure_generator import create_figure_if_none_given


def main():
    path_to_csv = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\out\dewatering_shape\dewatering_ramping_rate.csv"
    dewatering_ramping_rate_csv: pd.DataFrame = pd.read_csv(path_to_csv, sep=",")

    cmap = ["#f0f9e8", "#bae4bc","#7bccc4", "#2b8cbe"]

    fig = px.bar(dewatering_ramping_rate_csv, x="experiment_id", y=["0-10", "10-20", "20-30", "> 30"], barmode="stack", color_discrete_sequence=cmap
                 )

    fig.update_layout(
        xaxis=dict(title="scenario"),
        yaxis=dict(title="area [m\u00b2]"),
        xaxis_tickangle=-45

    )
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01), legend_title_text="Dewatering ramping rate [cm/h]")
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
        "boxplot_dewatering.svg",
        format="svg",
        width=1500,
        height=1500,
        scale=2,
    )

    fig.show()


if __name__ == "__main__":
    main()