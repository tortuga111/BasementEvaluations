from typing import Sequence, Iterable

import geopandas as gpd
import numpy as np
import shapely
from shapely import ops
from shapely.geometry import MultiPoint, Point, LineString, MultiLineString

from script_for_profile_creation import filter_points_with_less_than_zero_elevation
from utils.loading import load_data_with_crs_2056
from utils.sampling import extract_elevation_from_raster
from water_surface_preparation.data_classes.enums import Scenario, ShoreTypes
from water_surface_preparation.data_classes.parameters import (
    ParametersForOneProcess,
    ParametersToAssignElevationToPoints,
    ParametersToFilterSamplingPoints,
)
from water_surface_preparation.data_classes.paths import PathsForOneProcess
from water_surface_preparation.data_classes.points_per_line import (
    ProjectedPointsPerCenterLine,
    OrderedProjectedPointsPerCenterLine,
    ProcessedPointsPerCenterLine,
    PointsPerCenterline,
)
from water_surface_preparation.filter import filter_outliers_from_elevation_points
from water_surface_preparation.plotting import (
    debug_plot,
    create_plot_for_transect_lines,
    plot_smooth_vs_raster_elevation,
    plot_interpolated_vs_smooth_and_raster_elevation,
)
from water_surface_preparation.sampling import sample_points_along_line
from water_surface_preparation.smoothing import smooth_elevations_along_line, apply_rolling_window_smoothing
from water_surface_preparation.transects import (
    calculate_transects,
    trim_intersecting_parts_of_transects,
    sample_points_for_along_all_transects,
)


def interpolate_elevation_from_nearest_points(
    shoreline_points_per_center_line: PointsPerCenterline,
    transect_points_with_elevation: gpd.GeoDataFrame,
    buffer_distance: float,
) -> gpd.GeoDataFrame:
    elevation_per_point = []
    for point in shoreline_points_per_center_line.points.geometry:
        point: Point
        buffer = point.buffer(buffer_distance)
        intersects = transect_points_with_elevation.intersects(buffer)
        elevation_per_point.append(transect_points_with_elevation.loc[intersects, "z_interpolated"].mean())

    return gpd.GeoDataFrame(
        {"z_interpolated": elevation_per_point}, geometry=shoreline_points_per_center_line.points.geometry
    )


def get_all_paths_for_one_scenario(demanded_scenario: Scenario) -> PathsForOneProcess:
    if demanded_scenario == Scenario.af_2021:
        return PathsForOneProcess(
            path_to_shoreline=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_shoreline\\shoreline_AF2021.shp"
            ),
            paths_to_centerlines=[
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_centerline\\centerline_sidechannel_01_AF2021_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_centerline\\centerline_sidechannel_02_AF2021_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_centerline\\centerline_sidechannel_03_AF2021_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_centerline\\centerline_sidechannel_04_AF2021_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_centerline\\centerline_mainchannel_AF2021_smooth.shp",
            ],
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "01_prep_raster\\AF_2021_dsm_AOIextended_resample.tif"
            ),
            path_to_additional_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01_AF2021_wettedarea\\AF2021_shoreline\\Hilfspunkte.shp"
            ),
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\03_create_tin\\04_evaluation_tin\\AF_2021_GPS_shoreline_with_z_raster.shp"
            ),
        )
    elif demanded_scenario == Scenario.af_2020:
        return PathsForOneProcess(
            path_to_shoreline=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_shoreline\\shoreline_AF2020.shp"
            ),
            paths_to_centerlines=[
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_centerline\\centerline_sidechannel_01_AF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_centerline\\centerline_sidechannel_02_AF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_centerline\\centerline_sidechannel_03_AF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_centerline\\centerline_sidechannel_04_AF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_centerline\\centerline_mainchannel_AF2020_smooth.shp",
            ],
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "01_prep_raster\\AF_2020_dsm_AOIextended_minus020.tif"
            ),
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\03_create_tin\\04_evaluation_tin\\AF_2020_GPS_shoreline_with_z_raster.shp"
            ),
            path_to_additional_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_shoreline\\AF2020_Hilfspunkte.shp"
            ),
        )

    elif demanded_scenario == Scenario.bf_2020:
        return PathsForOneProcess(
            path_to_shoreline=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_shoreline\\BF2020_shoreline.shp"
            ),
            paths_to_centerlines=[
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_centerline\\centerline_sidechannel_01_BF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_centerline\\centerline_sidechannel_02_BF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_centerline\\centerline_sidechannel_03_BF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_centerline\\centerline_sidechannel_04_BF2020_smooth.shp",
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_centerline\\centerline_mainchannel_BF2020_smooth.shp",
            ],
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\" "01_prep_raster\\BF_2020_dsm_AOIextended.tif"
            ),
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\03_create_tin\\04_evaluation_tin\\BF_2020_GPS_shoreline_with_z_raster.shp"
            ),
            path_to_additional_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\"
                "02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_shoreline\\BF2020_Hilfspunkte.shp"
            ),
        )

    else:
        raise NotImplementedError(f"{Scenario} is not implemented yet")


def order_points_from_line_origin_on(
    projected_points_by_center_line: ProjectedPointsPerCenterLine,
) -> OrderedProjectedPointsPerCenterLine:
    projected_points_by_center_line.projected_points.reset_index(inplace=True)
    projected_points_by_center_line.projected_points["distance"] = np.nan
    for index, row in projected_points_by_center_line.projected_points.iterrows():
        distance = projected_points_by_center_line.center_line.project(row.geometry).values[0]
        projected_points_by_center_line.projected_points.loc[index, "distance"] = distance

    ordered_points = projected_points_by_center_line.projected_points.sort_values(by="distance").reset_index(drop=True)
    return OrderedProjectedPointsPerCenterLine(
        projected_points=ordered_points,
        center_line=projected_points_by_center_line.center_line,
    )


def interpolate_elevation(
    points_to_add_elevation: gpd.GeoDataFrame, points_to_get_elevation_from: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    points_to_add_elevation["z_interpolated"] = np.interp(
        points_to_add_elevation["distance"],
        points_to_get_elevation_from["distance"],
        points_to_get_elevation_from["z_smooth"],
    )
    return points_to_add_elevation


def create_all_parameters() -> ParametersForOneProcess:
    return ParametersForOneProcess(
        sampling_distance=2,
        demanded_scenario=Scenario.bf_2020,
        buffer_distance=45,
        line_length=45,
        frac=0.2,
        parameters_to_assign_elevation_to_points=ParametersToAssignElevationToPoints(buffer_distance=6),
        parameters_to_filter_sampling_points=ParametersToFilterSamplingPoints(
            buffer_distance=30, maximal_deviation=0.25
        ),
    )


def main():
    parameters = create_all_parameters()
    paths = get_all_paths_for_one_scenario(parameters.demanded_scenario)
    smoothen_with_lowess_ = True
    shoreline = load_data_with_crs_2056(paths.path_to_shoreline)
    debug_plot(shoreline, "shoreline")

    open_shore_shoreline = shoreline[shoreline["shore_type"] == ShoreTypes.open_shore.value]

    points_without_elevation = sample_points_along_line(
        open_shore_shoreline, sampling_distance=parameters.sampling_distance
    )
    points_with_elevation = extract_elevation_from_raster(points_without_elevation, path_to_raster=paths.path_to_raster)
    filtered_points_with_elevation = filter_outliers_from_elevation_points(
        points_with_elevation,
        parameters.parameters_to_filter_sampling_points.buffer_distance,
        parameters.parameters_to_filter_sampling_points.maximal_deviation,
    )
    filtered_points_with_elevation.to_file(f"{parameters.demanded_scenario.value}_filtered_open_dsm_points.shp")
    filtered_points_with_elevation_and_additional_points = append_additional_points_if_available(
        filtered_points_with_elevation, paths
    )
    center_lines = load_all_center_lines(paths.paths_to_centerlines)
    shoreline_points_per_center_line = assign_points_to_center_lines(
        center_lines,
        filtered_points_with_elevation_and_additional_points,
        parameters.buffer_distance,
        does_have_z_raster=True,
    )
    gps_points_per_line = []
    if paths.path_to_gps_points is not None:
        gps_points = load_data_with_crs_2056(paths.path_to_gps_points)
        gps_points_per_center_line = assign_points_to_center_lines(
            center_lines, gps_points, parameters.buffer_distance, does_have_z_raster=True
        )
        for i, line_matched_with_gps_points in enumerate(gps_points_per_center_line):
            are_there_any_gps_points = len(line_matched_with_gps_points.points.index) > 0
            if are_there_any_gps_points:
                debug_plot(line_matched_with_gps_points.points, f"line_matched_with_gps_points{i}")
                projected_points = project_matched_points_on_center_line(line_matched_with_gps_points)
                ordered_gps_points = order_points_from_line_origin_on(projected_points)
                gps_points_per_line.append(ordered_gps_points)
            else:
                gps_points_per_line.append(
                    OrderedProjectedPointsPerCenterLine(
                        line_matched_with_gps_points.points, line_matched_with_gps_points.center_line
                    )
                )
    else:
        gps_points_per_line.append(OrderedProjectedPointsPerCenterLine(gpd.GeoDataFrame(), gpd.GeoDataFrame()))
    transects_per_line = []
    for i, (line_matched_with_shore_points, line_matched_with_gps_points) in enumerate(
        zip(shoreline_points_per_center_line, gps_points_per_line)
    ):
        debug_plot(line_matched_with_shore_points.points, f"line_matched_with_shore_points.points{i}")
        debug_plot(line_matched_with_shore_points.center_line, f"line_matched_with_points_center_line{i}")
        line_matched_with_shore_points.points.to_file(f"out\\shore_points_per_{i}_th_center_line.shp")
        projected_points = project_matched_points_on_center_line(line_matched_with_shore_points)
        ordered_projected_points = order_points_from_line_origin_on(projected_points)
        if smoothen_with_lowess_:
            processed_center_points = smooth_elevations_along_line(ordered_projected_points, parameters.frac)
        else:
            processed_center_points = apply_rolling_window_smoothing(ordered_projected_points)

        points_along_center_line = sample_points_along_line(
            line_matched_with_shore_points.center_line, parameters.sampling_distance
        )
        points_along_center_line_with_center_line = ProjectedPointsPerCenterLine(
            points_along_center_line, line_matched_with_shore_points.center_line
        )
        points_along_center_line_ordered = order_points_from_line_origin_on(points_along_center_line_with_center_line)
        points_with_elevation = interpolate_elevation(
            points_along_center_line_ordered.projected_points, processed_center_points.projected_points
        )
        interpolated_points_along_center_line_with_center_line = ProcessedPointsPerCenterLine(
            points_with_elevation, line_matched_with_shore_points.center_line
        )
        interpolated_points_along_center_line_with_center_line.projected_points.to_file(
            f"out\\points_along_{i}_th_center_line.shp"
        )

        transect_lines_and_points = calculate_transects(
            interpolated_points_along_center_line_with_center_line.projected_points, parameters.line_length
        )
        create_plot_for_transect_lines(transect_lines_and_points, i)

        transect_lines_and_points_free_of_intersections = trim_intersecting_parts_of_transects(
            transect_lines_and_points
        )
        transects_per_line.append(transect_lines_and_points_free_of_intersections)
        create_plot_for_transect_lines(transect_lines_and_points_free_of_intersections, 100 - i)

        # add Dsm points on center line for the center line plot
        interpolated_points_along_center_line_with_dsm_value = extract_elevation_from_raster(
            interpolated_points_along_center_line_with_center_line.projected_points, path_to_raster=paths.path_to_raster
        )
        filtered_interpolated_points_along_center_line_with_dsm_value = filter_points_with_less_than_zero_elevation(
            interpolated_points_along_center_line_with_dsm_value
        )

        are_there_any_gps_points = len(line_matched_with_gps_points.projected_points.index) > 0
        if are_there_any_gps_points:
            plot_smooth_vs_raster_elevation(
                i,
                processed_center_points,
                interpolated_points_along_center_line_with_center_line,
                filtered_interpolated_points_along_center_line_with_dsm_value,
                line_matched_with_gps_points.projected_points,
            )
        else:
            plot_smooth_vs_raster_elevation(
                i,
                processed_center_points,
                interpolated_points_along_center_line_with_center_line,
                filtered_interpolated_points_along_center_line_with_dsm_value,
                None,
            )
        plot_interpolated_vs_smooth_and_raster_elevation(
            i, interpolated_points_along_center_line_with_center_line, processed_center_points
        )

    open_or_covered_shoreline = shoreline.loc[
        (shoreline["shore_type"] == ShoreTypes.open_shore.value) | (shoreline["shore_type"] == ShoreTypes.covered.value)
    ]

    points_along_shoreline = sample_points_along_line(open_or_covered_shoreline, parameters.sampling_distance)
    shoreline_points_per_center_line = assign_points_to_center_lines(
        center_lines, points_along_shoreline, parameters.buffer_distance
    )

    all_shore_line_points_with_elevation = gpd.GeoDataFrame(crs=shoreline.crs)
    for shoreline_points_per_center_line, transects_per_center_line in zip(
        shoreline_points_per_center_line, transects_per_line
    ):
        transect_points_with_elevation = sample_points_for_along_all_transects(
            transects_per_center_line, parameters.sampling_distance
        )
        shore_line_points_with_elevation = interpolate_elevation_from_nearest_points(
            shoreline_points_per_center_line, transect_points_with_elevation, parameters.buffer_distance
        )
        # for each point on shoreline, interpolate elevation from transects
        all_shore_line_points_with_elevation = all_shore_line_points_with_elevation.append(
            shore_line_points_with_elevation
        )
    all_shore_line_points_with_elevation.to_file(
        f"out\\interpolated_shore_line_points_{parameters.demanded_scenario.value}.shp"
    )

    debug_plot(open_shore_shoreline, "open_shore_shoreline")
    debug_plot(open_or_covered_shoreline, "open_or_covered_shoreline")
    debug_plot(all_shore_line_points_with_elevation, "all_shore_line_points_with_elevation")


def append_additional_points_if_available(filtered_points_with_elevation, paths):
    if paths.path_to_additional_points is not None:
        additional_points = load_data_with_crs_2056(paths.path_to_additional_points)
        filtered_points_with_elevation_and_additional_points = filtered_points_with_elevation.append(additional_points)
    else:
        filtered_points_with_elevation_and_additional_points = filtered_points_with_elevation
    return filtered_points_with_elevation_and_additional_points


def load_all_center_lines(paths_to_center_lines: Iterable[str]) -> list[gpd.GeoDataFrame]:
    center_lines = [load_data_with_crs_2056(path) for path in paths_to_center_lines]
    merged_center_lines = []
    for center_line in center_lines:
        merged_lines = ops.linemerge([geom for geom in center_line.geometry])
        if isinstance(merged_lines, MultiLineString):
            merged_lines = __join_a_line(merged_lines)
        merged = {"geometry": [merged_lines]}
        merged_center_lines.append(gpd.GeoDataFrame(merged, crs=center_line.crs))
    return merged_center_lines


def __join_a_line(multiline_string: MultiLineString) -> LineString:
    coordinates = [list(i.coords) for i in multiline_string]
    return shapely.geometry.LineString([coordinate for sublist in coordinates for coordinate in sublist])


def assign_points_to_center_lines(
    center_lines: Sequence[gpd.GeoDataFrame],
    points: gpd.GeoDataFrame,
    buffer_distance: float,
    does_have_z_raster: bool = False,
) -> list[PointsPerCenterline]:
    matched_points_per_line = {i: [] for i in range(len(center_lines))}
    elevation_of_matched_points_per_line = {i: [] for i in range(len(center_lines))}

    buffered_lines = []
    for line in center_lines:
        buffered_lines.append(line.buffer(buffer_distance, cap_style=2))

    for index, row in points.iterrows():
        distances = []
        if isinstance(row.geometry, Point):
            for line, buffer in zip((center_line.geometry[0] for center_line in center_lines), buffered_lines):
                assert isinstance(line, LineString)
                if buffer.intersects(row.geometry).any():
                    distances.append(row.geometry.distance(line))
                else:
                    distances.append(np.inf)
            this_point_is_outside_of_all_buffers = np.min(distances) >= np.inf
            if this_point_is_outside_of_all_buffers:
                continue
            matching_index: int = np.argmin(distances)  # noqa
            matched_points_per_line[matching_index].append(row.geometry)
            # TODO: check input dataframe with points if there is a z_raster column. Get rid of does have z_raster parameter.
            z_raster = row["z_raster"] if does_have_z_raster else np.nan
            elevation_of_matched_points_per_line[matching_index].append(z_raster)

    converted_points = [
        gpd.GeoDataFrame(
            {"z_raster": elevation_of_matched_points_per_line[key], "geometry": matched_points_per_line[key]},
            crs=center_lines[0].crs,
        )
        for key in matched_points_per_line.keys()
    ]

    points_per_center_lines = [
        PointsPerCenterline(points=points, center_line=center_line)
        for center_line, points in zip(center_lines, converted_points)
    ]
    return points_per_center_lines


def project_matched_points_on_center_line(
    matched_points_per_center_line: PointsPerCenterline,
) -> ProjectedPointsPerCenterLine:
    projected_points = matched_points_per_center_line.points.copy()
    if len(matched_points_per_center_line.points.index) > 0:
        projected_points["geometry"] = projected_points.apply(
            lambda row: matched_points_per_center_line.center_line.interpolate(
                matched_points_per_center_line.center_line.project(row.geometry)
            ),
            axis=1,
        )
    return ProjectedPointsPerCenterLine(projected_points, matched_points_per_center_line.center_line)


if __name__ == "__main__":
    main()
