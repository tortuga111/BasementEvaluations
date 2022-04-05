import os

import pandas as pd
import plotly.express as px
from plotly.graph_objs import Figure


def get_data_path() -> str:
    return os.path.join(os.getcwd(), "data")


def _create_data_path() -> str:
    return os.path.join(
        os.path.join(os.getcwd(), "../../../../02_Data/02_prep_bathy/01_AF2021_wettedarea/GPS_shoreline_pts")
    )


def do_scatter_plot_for_data_frame(df: pd.DataFrame, x_name: str, y1_name: str) -> Figure:
    figure = px.scatter(df, x=x_name, y=y1_name)
    return figure


def do_line_plot_for_data_frame(df: pd.DataFrame, x_name: str, y_name: str) -> Figure:
    figure = px.line(df, x=xname, y=y_name)
    figure.update_xaxes(range=[0, 1])
    figure.update_yaxes(range=[0, 1])
    return figure


def do_bar_plot_for_data_frame(df: pd.DataFrame, x_name: str, y_name: str) -> Figure:
    figure = px.bar(df, x=x_name, y=y_name)
    figure.update_xaxes(range=[0, 1])
    figure.update_yaxes(range=[0, 1])
    return figure


def _load_and_plot_data() -> None:
    filename = "pts_shoreline_withelev_AF21.csv"
    # id,x,y,z,wassertief,SAMPLE_ele

    x_name = "z"
    y1_name = "SAMPLE_ele"

    raw_df = pd.read_csv(os.path.join(_create_data_path(), filename))

    do_scatter_plot_for_data_frame(raw_df, x_name, y1_name).show()


if __name__ == "__main__":
    _load_and_plot_data()
