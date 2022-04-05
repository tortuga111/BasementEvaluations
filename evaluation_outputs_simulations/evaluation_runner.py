import glob
import pickle

import geopandas as gpd

from script_for_profile_creation import OrderedProjectedGpsPointsPerProfileLine
from utils.loading import load_data_with_crs_2056


def main():
    path_to_bottom_elevation = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\06_test_run_hw20_new_mesh\\discharge_file@hydrograph_continue_HW20_plus2_5pc.txt$default_friction@35.0$end@1000\\evaluation\\bottom_elevation.shp"
    path_to_hydraulic_state = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\06_test_run_hw20_new_mesh\\discharge_file@hydrograph_continue_HW20_plus2_5pc.txt$default_friction@35.0$end@1000\\evaluation\\hydraulic_state.shp"
    path_to_flow_velocity = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\06_test_run_hw20_new_mesh\\discharge_file@hydrograph_continue_HW20_plus2_5pc.txt$default_friction@35.0$end@1000\\evaluation\\flow_velocity.shp"

    bottom_elevation = load_data_with_crs_2056(path_to_bottom_elevation)
    hydraulic_state = load_data_with_crs_2056(path_to_hydraulic_state)
    flow_velocity = load_data_with_crs_2056(path_to_flow_velocity)
    print(bottom_elevation.describe())
    print(hydraulic_state.describe())
    print(flow_velocity.head())

    initial_hydraulic_state = "0000000-Va"
    initial_bottom_elevation = "0000000-Bo"
    last_hydraulic_state = "0000003-Va"
    last_bottom_elevation = "0000003-Bo"

    new_shape_file = gpd.GeoDataFrame(geometry=bottom_elevation.geometry, crs=2056)
    new_shape_file["area"] = new_shape_file.area
    new_shape_file["wd_bf"] = hydraulic_state[initial_hydraulic_state] - bottom_elevation[initial_bottom_elevation]
    new_shape_file["wd_af"] = hydraulic_state[last_hydraulic_state] - bottom_elevation[last_bottom_elevation]
    new_shape_file["delta_z"] = bottom_elevation[last_bottom_elevation] - bottom_elevation[initial_bottom_elevation]

    print(new_shape_file.describe())
    print(new_shape_file.loc[new_shape_file["wd_bf"] > 0, :].describe())
    print(new_shape_file.loc[new_shape_file["wd_af"] > 0, :].describe())
    print(new_shape_file["delta_z"].describe())
    total_area = new_shape_file["area"].sum()
    print("the total area is:", total_area)

    for file_name in glob.glob("..\\river_profiles_from_bathymetry\\points_with_line*"):
        with open(file_name, "rb") as dump_file:
            points_with_line: OrderedProjectedGpsPointsPerProfileLine = pickle.load(dump_file)
            delta_z_values = []
            for index, point in enumerate(points_with_line.projected_gps_points.geometry):
                value = new_shape_file.loc[new_shape_file.contains(point), "delta_z"].values[0]
                delta_z_values.append(value)
            points_with_line.projected_gps_points["delta_z"] = delta_z_values

            


            points_with_line.projected_gps_points.to_file("out\\profile_points_with_mesh_information.shp")
            print("this worked.")


# copy attributes

# calculate water depth


if __name__ == "__main__":
    main()
