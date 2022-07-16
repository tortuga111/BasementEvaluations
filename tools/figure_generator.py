from typing import Optional

from plotly import graph_objects as go


def generate_figure_template() -> go.Figure:
    layout = {"legend":dict(yanchor="top", y=0.99, xanchor="left", x=0.01), "showlegend": True, "hovermode": "closest", "plot_bgcolor": "#f2f2f2",
              "margin": dict(l=1, r=1, b=1, t=1), "font":dict(size=20),}
    return go.Figure(layout=layout)


def scale_axis_equal(figure: go.Figure) -> None:
    figure.update_yaxes(
        scaleanchor="x",
        scaleratio=1,
    )


def create_figure_if_none_given(figure: Optional[go.Figure] = None) -> go.Figure:
    return generate_figure_template() if figure is None else figure
