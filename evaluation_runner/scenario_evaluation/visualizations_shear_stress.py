import pandas as pd
from geopandas import GeoDataFrame
from plotly import graph_objects as go


def create_scatter_plot_shear_stress(path_to_csv_shear_stress_results: str):
    shear_stress_results: pd.DataFrame = pd.read_csv(path_to_csv_shear_stress_results, sep=";")
    shear_stress_results.drop(index=0, inplace=True)
    fig = go.Figure()
    traces = [
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["wetted_area"],
            mode="lines",
            name="total wetted area",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_10Nm"],
            mode="lines",
            name="10Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_20Nm"],
            mode="lines",
            name="20Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_30Nm"],
            mode="lines",
            name="30Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_40Nm"],
            mode="lines",
            name="40Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_50Nm"],
            mode="lines",
            name="50Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_60Nm"],
            mode="lines",
            name="60Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_70Nm"],
            mode="lines",
            name="70Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_80Nm"],
            mode="lines",
            name="80Nm",
            fill="tonexty",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_90Nm"],
            mode="lines",
            name="90Nm",
            fill="tonexty",
        ),
    ]
    fig.add_traces(list(reversed(traces)))
    fig.update_layout(
        xaxis=dict(title="discharge [m\u00b3/s]", range=[1, None]),
        yaxis=dict(title="area [m\u00b3]"),
    )
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    fig.update_layout(
        autosize=True,
        margin=dict(l=1, r=1, b=1, t=1, pad=4),
        paper_bgcolor="LightSteelBlue",
        font=dict(
            size=20,
        ),
    )
    fig.write_image(
        "..\\..\\out\\plots_shieldstress\\lineplot_shear_stress.svg", format="svg", width=1200, height=900, scale=2
    )
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default

    fig.show()


def main():
    path_to_csv_shear_stress_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\.logs\log_shear_stress_fine_mesh.csv"

    create_scatter_plot_shear_stress(path_to_csv_shear_stress_results)


if __name__ == "__main__":
    main()


def another_function_that_will_sexually_embarrass_me(some_df: GeoDataFrame) -> None:
    upper_bounds_for_tau = list(range(0, 100, 10))
    trajectories_to_plot = {bound: [] for bound in upper_bounds_for_tau}
    discharge_steps = []
    for discharge, group in some_df.groupby("discharge"):
        discharge_steps.append(discharge)
        for bound in upper_bounds_for_tau:
            df_with_lower_chezy = group.drop(group[group["tau_chezy"] > bound].index)
            trajectories_to_plot[bound].append(df_with_lower_chezy.area.sum())

    fig = go.Figure()
    fig.add_traces(
        [go.Scatter(x=discharge_steps, y=values,name=f"{key}_some_unit", fill="tonexty", mode="none") for key, values in trajectories_to_plot.items() ]
    )
    fig.show()
