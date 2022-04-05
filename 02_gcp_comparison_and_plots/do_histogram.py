import os

import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px


def do_histogram_with_variance(path_to_points: str):
    file_to_compare = gpd.read_file(path_to_points)
    file_to_compare["difference_z"] = 0.0
    file_to_compare["difference_z"] = file_to_compare["z_raster"] - file_to_compare["z"]

    plt.hist(file_to_compare["difference_z"], bins=10)
    plt.show()

    figure = px.histogram(file_to_compare, x="difference_z")
    figure.show()


def main() -> None:
    path_to_points: str = os.path.join(
        os.getcwd(),
        "..\\..\\..\\..\\02_Data//02_prep_bathy//03_create_tin//02_evaluation_tin" "//points_with_raster_values1.shp",
    )

    path_to_results: str = os.path.join(
        os.getcwd(), "..\\..\\..\\..\\02_Data//02_prep_bathy//03_create_tin//02_evaluation_tin"
    )

    do_histogram_with_variance(path_to_points)


if __name__ == "__main__":
    main()
