import geopandas as gpd

from csv_logging.calculate_entries import (
    goodness_of_fit_for_velocity,
    goodness_of_fit_for_bottom_elevation,
    goodness_of_fit_for_water_depth,
)
from csv_logging.csvlogger import (
    CSVLogger,
    GoodnessOfFitForInitialVelocity,
    GoodnessOfFitForInitialBottomElevation,
    GoodnessOfFitForInitialWaterDepth,
)
from evaluation_runner.profiles.evaluate_profiles import (
    create_histogram_with_mesh_values,
)
from voud.load_result_shapes import load_data_from_simulations
from extract_data.summarising_mesh import assign_requested_values_from_summarising_mesh_to_point
from utils.loading import load_data_with_crs_2056


def main():
    raise NotImplementedError
    logger_goodness_of_fit_for_bottom_elevation = CSVLogger(GoodnessOfFitForInitialBottomElevation)
    logger_goodness_of_fit_for_water_depth = CSVLogger(GoodnessOfFitForInitialWaterDepth)
    logger_goodness_of_fit_for_velocity = CSVLogger(GoodnessOfFitForInitialVelocity)

    # load data
    bottom_elevation, flow_velocity, hydraulic_state = load_data_from_simulations()
    path_to_gps_points = r"C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\BF2020\\GPS_transects_BF2020_selection_4transectsshp.shp"

    mesh_with_all_results = create_summarising_mesh_with_all_results(bottom_elevation, flow_velocity, hydraulic_state)

    columns_to_lookup = ["bot_ele_t0", "wse_t0", "v_t0", "wd_t0"]
    mapping = {"bot_ele": "bot_ele_t0", "wse": "wse_t0", "v": "v_t0", "wd": "wd_t0"}
    assert set(columns_to_lookup).difference(mapping.values()).__len__() == 0
    renamed_updated_gps_points = assign_requested_values_from_summarising_mesh_to_point(
        columns_to_lookup, mesh_with_all_results, points=load_data_with_crs_2056(path_to_gps_points)
    ).rename(columns={v: k for k, v in mapping.items()})

    # relabel columns (get rid of time)

    renamed_updated_gps_points["wd_sim_gps"] = renamed_updated_gps_points["wd"] - renamed_updated_gps_points["WT_m_"]
    gps_points_with_velocity: gpd.GeoDataFrame = renamed_updated_gps_points.loc[
        renamed_updated_gps_points["Vel__m_s_"] > 0, :
    ]
    gps_points_with_velocity = gps_points_with_velocity.copy(deep=True)
    gps_points_with_velocity["v_sim_gps"] = gps_points_with_velocity["v"] - gps_points_with_velocity["Vel__m_s_"]

    create_histogram_with_mesh_values(renamed_updated_gps_points, "wd")
    create_histogram_with_mesh_values(renamed_updated_gps_points, "wd_sim_gps")
    create_histogram_with_mesh_values(gps_points_with_velocity, "v_sim_gps")

    logger_goodness_of_fit_for_water_depth.add_entry_to_log(goodness_of_fit_for_water_depth(renamed_updated_gps_points))
    logger_goodness_of_fit_for_velocity.add_entry_to_log(goodness_of_fit_for_velocity(gps_points_with_velocity))
    logger_goodness_of_fit_for_bottom_elevation.add_entry_to_log(
        goodness_of_fit_for_bottom_elevation(renamed_updated_gps_points)
    )

    logger_goodness_of_fit_for_velocity.write_logs_as_csv_to_file("log_initial_goodness_of_fit_bf2020_velocities.csv")
    logger_goodness_of_fit_for_water_depth.write_logs_as_csv_to_file(
        "log_initial_goodness_of_fit_bf2020_water_depths.csv"
    )
    logger_goodness_of_fit_for_bottom_elevation.write_logs_as_csv_to_file(
        "log_initial_goodness_of_fit_bf2020_bottom_ele.csv"
    )


if __name__ == "__main__":
    main()
