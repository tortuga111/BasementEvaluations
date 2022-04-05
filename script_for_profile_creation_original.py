from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Union

import geopandas
import geopandas as gpd
import numpy as np
import statsmodels.regression.linear_model
from geopandas import GeoDataFrame
from numpy import mean
from plotly import graph_objs as go
from plotly.graph_objs import Scatter, Figure, Scatter3d
from scipy.optimize import NonlinearConstraint, minimize
from scipy.spatial import KDTree
from shapely.geometry import LineString, MultiLineString

from utils.loading import load_data_with_crs_2056
from utils.sampling import extract_elevation_from_raster


class ProfileScenario(Enum):
    bf_2020 = "BF2020"
    af_2020 = "AF2020"


@dataclass(frozen=True)
class PathsForProfileCreation:
    path_to_raster: str
    path_to_gps_points: str
    path_to_water_mask: str
    scenario_id: ProfileScenario


def create_paths(demanded_scenario: ProfileScenario) -> PathsForProfileCreation:
    path_to_gps_points = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\AF2020\\201102_sarine_nachflut_transects.shp"
    path_to_raster = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\02_test_run_hw2020\\test01_af20_bottom_elevation.tif"
    path_to_water_mask = "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_shoreline\\wetted_area_AF2020.shp"
    return PathsForProfileCreation(
        path_to_raster, path_to_gps_points, path_to_water_mask, scenario_id=ProfileScenario.af_2020
    )

    if demanded_scenario == Scenario.bf_2020:
        return PathsForProfileCreation(
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\AF2020\\201102_sarine_nachflut_transects.shp"
            ),
            path_to_water_mask=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_shoreline\\wetted_area_AF2020.shp"
            ),
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\02_test_run_hw2020\\test01_af20_bottom_elevation.tif"
            ),
        )
    elif demanded_scenario == Scenario.af_2020:
        return PathsForProfileCreation(
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\AF2020\\201102_sarine_nachflut_transects.shp"
            ),
            path_to_water_mask=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_shoreline\\wetted_area_AF2020.shp"
            ),
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\04_Model_220309\\04_Model\\04_export_files\\02_test_run_hw2020\\test01_af20_bottom_elevation.tif"
            ),
        )


def rename_z_raster_column(gps_points_with_elevation: GeoDataFrame, scenario_id: ProfileScenario) -> GeoDataFrame:
    new_column_name = f"z_{scenario_id.value}"
    gps_points_with_elevation[new_column_name] = gps_points_with_elevation["z_raster"]
    gps_points_with_elevation[f"{scenario_id.value}-GPS"] = (
        gps_points_with_elevation[f"z_{scenario_id.value}"] - gps_points_with_elevation["H"]
    )
    return gps_points_with_elevation


def merge_pairs_if_a_common_point_exists(pairs: list[tuple[int, int]]) -> list[set[int]]:
    sets = [set(lst) for lst in pairs if lst]
    merged = True
    while merged:
        merged = False
        results = []
        while sets:
            common, rest = sets[0], sets[1:]
            sets = []
            for x in rest:
                if x.isdisjoint(common):
                    sets.append(x)
                else:
                    merged = True
                    common |= x
            results.append(common)
        sets = results
    return sets


def merge_all_points_to_lines_that_are_close_enough(gps_points: GeoDataFrame) -> list[set[int]]:
    pairs = KDTree(np.array(list(gps_points.geometry.apply(lambda point: (point.x, point.y))))).query_pairs(r=3)
    return merge_pairs_if_a_common_point_exists(pairs)  # noqa


def fit_a_line_to_the_points(x: Iterable[float], y: Iterable[float], segment_length: int) -> LineString:
    def calc_distance_from_point_set(v_):
        # v_ is accepted as 1d array to make easier with scipy.optimize
        # Reshape into two points
        v = (v_[:2].reshape(2, 1), v_[2:].reshape(2, 1))

        # Calculate t* for s(t*) = v_0 + t*(v_1-v_0), for the line segment w.r.t each point
        t_star_matrix = np.minimum(
            np.maximum(np.matmul(P - v[0].T, v[1] - v[0]) / np.linalg.norm(v[1] - v[0]) ** 2, 0), 1
        )
        # Calculate s(t*)
        s_t_star_matrix = v[0] + ((t_star_matrix.ravel()) * (v[1] - v[0]))

        # Take distance between all points and respective point on segment
        distance_from_every_point = np.linalg.norm(P.T - s_t_star_matrix, axis=0)
        return np.sum(distance_from_every_point)

    P = np.stack([x, y], axis=1)
    segment_length_constraint = NonlinearConstraint(
        fun=lambda x: np.linalg.norm(np.array([x[0], x[1]]) - np.array([x[2], x[3]])),
        lb=[segment_length],
        ub=[segment_length],
    )
    point = minimize(
        calc_distance_from_point_set,
        (0.0, -0.0, 1.0, 1.0),
        options={"maxiter": 1000, "disp": True},
        constraints=segment_length_constraint,
    ).x
    # plt.scatter(x, y)
    # plt.plot([point[0], point[2]], [point[1], point[3]])
    return LineString(([point[0], point[1]], [point[2], point[3]]))


@dataclass(frozen=True)
class PointsPerProfile:
    gps_points: gpd.GeoDataFrame
    profile_line: LineString


@dataclass(frozen=True)
class ProjectedPointsPerProfileLine:
    projected_gps_points: gpd.GeoDataFrame
    profile_line: LineString


def project_matched_points_on_profile_line(
    matched_points_per_profile_line: PointsPerProfile,
) -> ProjectedPointsPerProfileLine:
    projected_points = matched_points_per_profile_line.gps_points.copy()
    if len(matched_points_per_profile_line.gps_points.index) > 0:
        projected_points["geometry"] = projected_points.apply(
            lambda row: matched_points_per_profile_line.profile_line.interpolate(
                matched_points_per_profile_line.profile_line.project(row.geometry)
            ),
            axis=1,
        )
    return ProjectedPointsPerProfileLine(projected_points, matched_points_per_profile_line.profile_line)

    # Calculate distance to origin: order_points_from_line_origin_on
    # Sort according to distance
    # plot


class OrderedProjectedGpsPointsPerProfileLine(ProjectedPointsPerProfileLine):
    pass


def order_gps_points_from_line_origin_on(
    projected_gps_points_on_profile_line: ProjectedPointsPerProfileLine,
) -> OrderedProjectedGpsPointsPerProfileLine:
    projected_gps_points_on_profile_line.projected_gps_points.reset_index(inplace=True)
    projected_gps_points_on_profile_line.projected_gps_points["distance"] = np.nan
    for index, row in projected_gps_points_on_profile_line.projected_gps_points.iterrows():
        distance = projected_gps_points_on_profile_line.profile_line.project(row.geometry)
        projected_gps_points_on_profile_line.projected_gps_points.loc[index, "distance"] = distance

    ordered_points = projected_gps_points_on_profile_line.projected_gps_points.sort_values(by="distance").reset_index(
        drop=True
    )
    return OrderedProjectedGpsPointsPerProfileLine(
        projected_gps_points=ordered_points,
        profile_line=projected_gps_points_on_profile_line.profile_line,
    )


def filter_points_with_less_than_zero_elevation(points: GeoDataFrame) -> GeoDataFrame:
    points_filtered = points[round(points["z_raster"]) > 0]
    points_filtered.reset_index(drop=True, inplace=True)
    return points_filtered


def main():
    paths = create_paths()
    gps_points = load_data_with_crs_2056(paths.path_to_gps_points)
    water_mask = load_data_with_crs_2056(paths.path_to_water_mask)

    gps_points_with_elevation = filter_points_with_less_than_zero_elevation(
        extract_elevation_from_raster(path_to_raster=paths.path_to_raster, points_to_intersect=gps_points)
    )

    prepared_gps_points_with_elevation = rename_z_raster_column(gps_points_with_elevation, paths.scenario_id)
    prepared_gps_points_with_elevation.to_file(
        f"river_profiles_from_bathymetry\\GPS_points_for_profile_comparison_{paths.scenario_id.value}.shp"
    )

    indices_of_points_per_line = merge_all_points_to_lines_that_are_close_enough(prepared_gps_points_with_elevation)
    figure = Figure()
    for group_id, group_of_points in enumerate(indices_of_points_per_line):
        points_per_line = GeoDataFrame(geometry=[], crs=gps_points.crs)
        for point_index in group_of_points:
            points_per_line = points_per_line.append(prepared_gps_points_with_elevation.loc[point_index])

        x = list(points_per_line.geometry.apply(lambda point: point.x))
        y = list(points_per_line.geometry.apply(lambda point: point.y))
        z = points_per_line["z_raster"]
        fitted_line = fit_a_line_to_the_points(x, y, segment_length=100)
        d = {"geometry": [fitted_line]}
        fitted_line_with_geometry = geopandas.GeoDataFrame(d, crs=gps_points.crs)
        clipped_profile_lines: gpd.GeoDataFrame = gpd.clip(fitted_line_with_geometry, water_mask, keep_geom_type=True)
        clipped_profile_line: Union[LineString, MultiLineString] = clipped_profile_lines.geometry[0]
        if isinstance(clipped_profile_line, LineString):
            candidate_lines = [clipped_profile_line]
        else:
            candidate_lines = [line for line in clipped_profile_line]
        for candidate_line in candidate_lines:
            legend_group = f"points_for_{group_id=}"
            figure.add_traces(
                [
                    Scatter3d(
                        x=x,
                        y=y,
                        z=z,
                        name=f"points_for_{group_id=}",
                        mode="markers",
                        legendgroup=legend_group,
                        hovertemplate=f"Profile {group_id=}",
                    ),
                    Scatter3d(
                        x=list(candidate_line.coords.xy),
                        y=list(candidate_line.coords.xy),
                        z=[mean(z), mean(z)],
                        name=f"line_for_{group_id=}",
                        mode="lines",
                        legendgroup=legend_group,
                        showlegend=False,
                    ),
                ]
            )
            print("wait")

            # combine in one class

            gps_points_with_profile_line = PointsPerProfile(points_per_line, candidate_line)
            projected_gps_points_on_profile_line = project_matched_points_on_profile_line(gps_points_with_profile_line)
            ordered_gps_points_on_profile_line = order_gps_points_from_line_origin_on(
                projected_gps_points_on_profile_line
            )
            # debug_plot(ordered_gps_points_on_profile_line.projected_gps_points, f"debug_plot_profiles{group_of_points}.jpg")

            plot_river_profile(
                ordered_gps_points_on_profile_line,
                f"river_profiles_from_bathymetry\\profile{paths.scenario_id.value}_{group_id=}.html",
            )

        # Project points from each segment onto the line:
    figure.write_html("river_profiles_from_bathymetry\\profiles_overview.html")

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=prepared_gps_points_with_elevation[f"{paths.scenario_id.value}-GPS"]))
    fig.update_layout(
        xaxis=dict(title="Difference_Bathy_GPS"),
        yaxis=dict(title="n"),
    )
    fig.show()
    print(prepared_gps_points_with_elevation[f"{paths.scenario_id.value}-GPS"].mean())

    prepared_gps_points_with_elevation["water_depth_TIN"] = (
        prepared_gps_points_with_elevation["z_TIN17"] - prepared_gps_points_with_elevation["z_raster"]
    )
    prepared_gps_points_with_elevation["difference_GPS_TIN"] = (
        prepared_gps_points_with_elevation["water_depth_TIN"] - prepared_gps_points_with_elevation["WT_m_"]
    )
    print(
        "mean difference between prepared GPS points and TIN elevation of the water surface:",
        prepared_gps_points_with_elevation["difference_GPS_TIN"].mean(),
    )
    print("statistics modelled water depth:", prepared_gps_points_with_elevation["water_depth_TIN"].describe())
    print("statistics measured water depth:", prepared_gps_points_with_elevation["WT_m_"].describe())
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=prepared_gps_points_with_elevation["water_depth_TIN"],
        )
    )
    fig.update_layout(
        xaxis=dict(title="water_depth_TIN"),
        yaxis=dict(title="n"),
    )
    fig.show()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=prepared_gps_points_with_elevation["WT_m_"].values,
            y=prepared_gps_points_with_elevation["water_depth_TIN"].values,
            name=f"WT_m_ vs water_depth_TIN",
            mode="markers",
        )
    )
    fig.show()
    prepared_gps_points_with_elevation.to_file("river_profiles_from_bathymetry\\points_with_water_depth.shp")

    regression_water_depth = statsmodels.regression.linear_model.OLS(
        prepared_gps_points_with_elevation["water_depth_TIN"], prepared_gps_points_with_elevation["WT_m_"]
    )
    res = regression_water_depth.fit()
    print(res.summary())


def plot_river_profile(ordered_gps_points_on_profile_line, filename: str):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points["z_raster"].values,
            name="z_raster",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points["H"].values,
            name="GPS elevation",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points["WSE__m_"].values,
            name="GPS WSE",
            mode="lines+markers",
        )
    )

    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points["z_TIN17"].values,
            name="TIN elevation",
            mode="lines+markers",
        )
    )

    figure.write_html(filename)


if __name__ == "__main__":
    main()
