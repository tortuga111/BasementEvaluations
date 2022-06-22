import pandas as pd
from plotly import graph_objects as go


def create_scatter_plot_shear_stress(path_to_csv_shear_stress_results: str):
    shear_stress_results: pd.DataFrame = pd.read_csv(path_to_csv_shear_stress_results, sep=";")
    shear_stress_results.drop(index=0, inplace=True)
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
        xaxis=dict(title=r"discharge $[\frac{$m^{3}$}{s}$", range=[1, None]),
        yaxis=dict(title="area [m^2^]"),
        font=dict(
            size=12,
        ),
    )
    fig.show()


def main():
    path_to_csv_shear_stress_results = r"C:\Users\nflue\Documents\Masterarbeit\03_Projects\MasterThesis\BasementEvaluations\.logs\log_shear_stress_k34.csv"

    create_scatter_plot_shear_stress(path_to_csv_shear_stress_results)


if __name__ == "__main__":
    main()
