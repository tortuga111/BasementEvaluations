from matplotlib import pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

from utils.loading import load_data_with_crs_2056


def main():
    path_to_file = (
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af_1.shp"
    )
    shape_file = load_data_with_crs_2056(path_to_file)

    m = shape_file.explore(
        column="polygon_nr",
        tooltip="polygon_nr",
        popup=True,
        cmap="Set1",
        style_kwds=dict(color="black"),
        crs="EPSG2056",
        tiles=None,
    )

    m.save("map_test.html")

    fig, ax = plt.subplots(1, 1)
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    shape_file.plot(
        column="polygon_nr",
        ax=ax,
        legend=True,
        figsize=(15,10),
    )
    plt.savefig("test.jpg")


if __name__ == "__main__":
    main()
