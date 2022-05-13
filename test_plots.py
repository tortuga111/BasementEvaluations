from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from plotly.subplots import make_subplots
import plotly.graph_objects as go

from utils.loading import load_data_with_crs_2056


def main():
    path_to_file = "C:\\Users\\nflue\\Documents\\Masterarbeit\\03_Projects\\MasterThesis\\BasementEvaluations\\out\\polygons\\elevation_change_discharge_file@Hydrograph_HW2020_115000.txt$end@111900$kst_regions@161027236$fixed_bed@82647707.shp"
    shape_file = load_data_with_crs_2056(path_to_file)

    fig, ax = plt.subplots(1, 1)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    shape_file.plot(
        column="comparison",
        ax=ax,
        legend=True,
        figsize=(15, 10),
        cmap="Set1",
    )
    plt.savefig("test.jpg")

    fig = make_subplots(rows=1, cols=2)

    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[4, 5, 6]), row=1, col=1)

    fig.add_trace(go.Scatter(x=[20, 30, 40], y=[50, 60, 70]), row=1, col=2)

    fig.update_layout(height=600, width=800, title_text="Side By Side Subplots")
    fig.write_image("fig1test.png")


if __name__ == "__main__":
    main()
