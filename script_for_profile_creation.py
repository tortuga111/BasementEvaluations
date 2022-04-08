import pickle
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Union

import geopandas
import geopandas as gpd
import numpy as np
import statsmodels.regression.linear_model
from geopandas import GeoDataFrame
from plotly import graph_objs as go
from plotly.graph_objs import Scatter, Figure
from scipy.optimize import NonlinearConstraint, minimize
from scipy.spatial import KDTree
from shapely.geometry import LineString, MultiLineString

from utils.loading import load_data_with_crs_2056
from utils.sampling import extract_elevation_from_raster


class BeforeOrAfterFloodScenario(Enum):
    bf_2020 = "BF2020"
    af_2020 = "AF2020"


@dataclass(frozen=True)
class PathsForProfileCreation:
    path_to_raster: str
    path_to_gps_points: str
    path_to_water_mask: str


def create_paths(demanded_scenario: BeforeOrAfterFloodScenario) -> PathsForProfileCreation:
    if demanded_scenario == BeforeOrAfterFloodScenario.bf_2020:
        return PathsForProfileCreation(
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\BF2020\\GPS_transects_BF2020_selection.shp"
            ),
            path_to_water_mask=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01b_BF2020_wettedarea\\BF2020_shoreline\\wetted_area_BF2020_neu.shp"
            ),
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\BF2020\\bathy_for_dod\\topo_to_raster_with_gravel_BF2020_with_gravel.tif"
            ),
        )
    elif demanded_scenario == BeforeOrAfterFloodScenario.af_2020:
        return PathsForProfileCreation(
            path_to_gps_points=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\AF2020\\201102_sarine_nachflut_transects.shp"
            ),
            path_to_water_mask=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\02_prep_bathy\\01a_AF2020_wettedarea\\AF2020_shoreline\\wetted_area_AF2020.shp"
            ),
            path_to_raster=(
                "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\AF2020\\topo_to_raster_with_gravel_AF2020.tif"
            ),
        )


def rename_z_raster_column(
    gps_points_with_elevation: GeoDataFrame, scenario_id: BeforeOrAfterFloodScenario
) -> GeoDataFrame:
    new_column_name = create_z_column_name(scenario_id)
    gps_points_with_elevation[new_column_name] = gps_points_with_elevation["z_raster"]
    del gps_points_with_elevation["z_raster"]
    gps_points_with_elevation[f"{scenario_id.value}-GPS"] = (
        gps_points_with_elevation[f"z_{scenario_id.value}"] - gps_points_with_elevation["H"]
    )
    return gps_points_with_elevation


def create_z_column_name(scenario_id: BeforeOrAfterFloodScenario) -> str:
    return f"z_{scenario_id.value}"


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
    pairs = KDTree(np.array(list(gps_points.geometry.apply(lambda point: (point.x, point.y))))).query_pairs(r=4)
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
    scenario_id = BeforeOrAfterFloodScenario.bf_2020
    tin_nr = "TIN20"
    paths = create_paths(scenario_id)
    gps_points = load_data_with_crs_2056(paths.path_to_gps_points)
    water_mask = load_data_with_crs_2056(paths.path_to_water_mask)

    gps_points_with_elevation = filter_points_with_less_than_zero_elevation(
        extract_elevation_from_raster(path_to_raster=paths.path_to_raster, points_to_intersect=gps_points)
    )

    prepared_gps_points_with_elevation = rename_z_raster_column(gps_points_with_elevation, scenario_id)
    prepared_gps_points_with_elevation.to_file(
        f"river_profiles_from_bathymetry\\GPS_points_for_profile_comparison_{scenario_id}.shp"
    )

    indices_of_points_per_line = merge_all_points_to_lines_that_are_close_enough(prepared_gps_points_with_elevation)
    figure = Figure()
    for group_id, group_of_points in enumerate(indices_of_points_per_line):
        points_per_line = GeoDataFrame(geometry=[], crs=gps_points.crs)
        for point_index in group_of_points:
            points_per_line = points_per_line.append(prepared_gps_points_with_elevation.loc[point_index])

        x = list(points_per_line.geometry.apply(lambda point: point.x))
        y = list(points_per_line.geometry.apply(lambda point: point.y))
        z = points_per_line[create_z_column_name(scenario_id)]
        fitted_line = fit_a_line_to_the_points(x, y, segment_length=100)
        assert fitted_line.length > 0
        d = {"geometry": [fitted_line]}
        fitted_line_with_geometry = geopandas.GeoDataFrame(d, crs=gps_points.crs)
        clipped_profile_lines: gpd.GeoDataFrame = gpd.clip(fitted_line_with_geometry, water_mask, keep_geom_type=True)
        clipped_profile_line: Union[LineString, MultiLineString] = clipped_profile_lines.geometry[0]
        if isinstance(clipped_profile_line, LineString):
            candidate_lines = [clipped_profile_line]
        else:
            start = clipped_profile_line[0].coords[0]
            end = clipped_profile_line[-1].coords[-1]
            candidate_lines = [LineString((start, end))]
        for line_id, candidate_line in enumerate(candidate_lines):
            legend_group = f"points_for_{group_id=}"
            figure.add_traces(
                [
                    Scatter(
                        x=x,
                        y=y,
                        name=f"points_for_{group_id=}",
                        mode="markers",
                        legendgroup=legend_group,
                        hovertemplate=f"Profile {group_id=}",
                    ),
                    Scatter(
                        x=list(candidate_line.coords.xy),
                        y=list(candidate_line.coords.xy),
                        name=f"line_for_{group_id=}",
                        mode="lines",
                        legendgroup=legend_group,
                        showlegend=False,
                    ),
                ]
            )

            # combine in one class

            gps_points_with_profile_line = PointsPerProfile(points_per_line, candidate_line)
            projected_gps_points_on_profile_line = project_matched_points_on_profile_line(gps_points_with_profile_line)
            ordered_gps_points_on_profile_line = order_gps_points_from_line_origin_on(
                projected_gps_points_on_profile_line
            )
            none_of_the_points_on_the_line = (
                ordered_gps_points_on_profile_line.projected_gps_points["distance"].sum() == 0
            )
            if none_of_the_points_on_the_line:
                continue
            # debug_plot(ordered_gps_points_on_profile_line.projected_gps_points, f"debug_plot_profiles{group_of_points}.jpg")

            filename = (
                f"river_profiles_from_bathymetry\\points_with_line_{scenario_id.value}_{group_id=}_{line_id=}.pkl"
            )
            with open(filename, "wb") as dump_file:
                pickle.dump(ordered_gps_points_on_profile_line, dump_file)

            plot_river_profile_with_tin(
                ordered_gps_points_on_profile_line,
                f"river_profiles_from_bathymetry\\profile{scenario_id.value}_{group_id=}_{line_id=}.html",
                tin_nr,
                scenario_id,
            )

        # Project points from each segment onto the line:
    figure.write_html(f"river_profiles_from_bathymetry\\profiles_overview_{scenario_id.value}.html")

    fig = go.Figure()
    fig.add_trace(go.Histogram(x=prepared_gps_points_with_elevation[f"{scenario_id.value}-GPS"]))
    fig.update_layout(
        xaxis=dict(title="Difference_Bathy_GPS"),
        yaxis=dict(title="n"),
    )
    fig.write_html(
        f"river_profiles_from_bathymetry\\histogram_of_difference_GPS_elevation_and_modelled_elevation_{scenario_id.value}.html"
    )
    prepared_gps_points_with_elevation[f"{scenario_id.value}-GPS"].mean()

    fit_a_regression_line_to_modelled_and_simulated_elevations(prepared_gps_points_with_elevation, scenario_id)


def fit_a_regression_line_to_modelled_and_simulated_elevations(
    prepared_gps_points_with_elevation, scenario_id: BeforeOrAfterFloodScenario
):
    regression_bed_elevation = statsmodels.regression.linear_model.OLS(
        prepared_gps_points_with_elevation[create_z_column_name(scenario_id)], prepared_gps_points_with_elevation["H"]
    )
    res = regression_bed_elevation.fit()
    print(res.summary())


def plot_river_profile_with_tin(
    ordered_gps_points_on_profile_line, filename: str, tin_nr: str, scenario_id: BeforeOrAfterFloodScenario
):
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=ordered_gps_points_on_profile_line.projected_gps_points["distance"].values,
            y=ordered_gps_points_on_profile_line.projected_gps_points[create_z_column_name(scenario_id)].values,
            name=create_z_column_name(scenario_id),
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
            y=ordered_gps_points_on_profile_line.projected_gps_points[f"z_{tin_nr}"].values,
            name="TIN elevation",
            mode="lines+markers",
        )
    )

    figure.write_html(filename)


if __name__ == "__main__":
    main()
