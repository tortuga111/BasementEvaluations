import pandas as pd
from geopandas import GeoDataFrame
from plotly import graph_objects as go

from tools.figure_generator import create_figure_if_none_given


def create_scatter_plot_shear_stress(path_to_csv_shear_stress_results: str):
    shear_stress_results: pd.DataFrame = pd.read_csv(path_to_csv_shear_stress_results, sep=",")
    shear_stress_results.drop(index=0, inplace=True)

    fig = create_figure_if_none_given()
    traces = [
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_D90"],
            mode="none",
            name="> 72 N/m\u00b2",
            fill="tonexty",
            fillcolor="#8c2d04",
            stackgroup = "one",
            opacity = 0.1
    ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["area_guenter_criterion_chezy"] - shear_stress_results["abs_area_tau_more_than_D90"],
            mode="none",
            name="55.0 - 72.0 N/m\u00b2",
            fill="tonexty",
            fillcolor="#ec7014",
            stackgroup="one",
            opacity=0.1
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_critical_shield_stress_chezy"] - shear_stress_results["area_guenter_criterion_chezy"],
            mode="none",
            name="26.6 - 54.9 N/m\u00b2 (\u03C4)".format(),
            fill="tonexty",
            fillcolor="#fec44f",
            stackgroup = "one"
    ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["wetted_area"] - shear_stress_results["abs_area_critical_shield_stress_chezy"],
            mode="none",
            name="0 - 26.5 N/m\u00b2",
            fill="tonexty",
            fillcolor="#ffffb2",
            stackgroup="one"
        ),
    ]
    fig.add_traces(list(reversed(traces)))
    fig.update_layout(
        xaxis=dict(title="discharge [m\u00b3/s]"),
        yaxis=dict(title="area [m\u00b2]"),
    )

    fig.write_image(
        "..\\..\\out\\plots_shieldstress\\lineplot_shear_stress_stacked.svg", format="svg", width=1200, height=900, scale=2
    )
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default

    fig.show()

    fig = create_figure_if_none_given()
    traces = [
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_critical_shield_stress_chezy"],
            mode="markers",
            name="critical shear stress dm",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["area_guenter_criterion_chezy"],
            mode="markers",
            name="critical shear stress guenter",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_D90"],
            mode="markers",
            name="critical shear stress d90",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["wetted_area"],
            mode="none",
            name="< 30 N/m\u00b2",
            fill="tonexty",
            fillcolor="#bae4bc",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_30Nm"],
            mode="none",
            name=">30 N/m\u00b2",
            fill="tonexty",
            fillcolor="#7bccc4",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_50Nm"],
            mode="none",
            name="> 50 N/m\u00b2",
            fill="tonexty",
            fillcolor="#43a2ca",
            opacity=0.6
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_tau_more_than_70Nm"],
            mode="none",
            name="> 70 N/m\u00b2",
            fill="tonexty",
            fillcolor="#0868ac",
        ),
    ]
    fig.add_traces(list(reversed(traces)))
    fig.update_layout(
        xaxis=dict(title="discharge [m\u00b3/s]"),
        yaxis=dict(title="area [m\u00b2]"),
    )

    fig.write_image(
        "..\\..\\out\\plots_shieldstress\\lineplot_shear_stress_absarea.svg", format="svg", width=1200, height=900,
        scale=2
    )
    # fig.update_traces(quartilemethod="exclusive")  # or "inclusive", or "linear" by default

    fig.show()



def create_percentage_plot_of_shear_stress_areas(path_to_csv_shear_stress_results):
    shear_stress_results: pd.DataFrame = pd.read_csv(path_to_csv_shear_stress_results, sep=",")
    shear_stress_results.drop(index=0, inplace=True)
    fig = create_figure_if_none_given()
    traces = [
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["area_guenter_criterion_chezy"],
            stackgroup='one',
            mode="none",
            name="> 55.5 N/m\u00b2",
            fill="tonexty",
            fillcolor="#41b6c4",
            groupnorm='percent'
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["abs_area_critical_shield_stress_chezy"] - shear_stress_results[
                "area_guenter_criterion_chezy"],
            stackgroup='one',
            mode="none",
            name="<= 55.5 N/m\u00b2",
            fill="tonexty",
            fillcolor="#a1dab4",
        ),
        go.Scatter(
            x=shear_stress_results["discharge"],
            y=shear_stress_results["wetted_area"] - shear_stress_results["abs_area_critical_shield_stress_chezy"],
            stackgroup='one',
            mode="none",
            name="<= 26.6 N/m\u00b2",
            fill="tonexty",
            fillcolor="#ffffcc",
        ),
    ]
    fig.add_traces(list(reversed(traces)))
    fig.update_layout(
        xaxis=dict(title="discharge [m\u00b3/s]", range=[0, None]),
        yaxis=dict(title="area [m\u00b2]"),
    )
    fig.show()


def main():
    path_to_csv_shear_stress_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\out\plots_shieldstress\log_shear_stress_fine_mesh11.csv"

    create_scatter_plot_shear_stress(path_to_csv_shear_stress_results)
    create_percentage_plot_of_shear_stress_areas(path_to_csv_shear_stress_results)


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
