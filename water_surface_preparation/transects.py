import math
from dataclasses import replace
from itertools import combinations
from typing import Sequence, Iterable

import geopandas as gpd
import numpy
from shapely.geometry import LineString, Point

from water_surface_preparation.sampling import sample_points_along_line
from utils import pairwise
from utils.angle_calculation import angle_between_two_points
from water_surface_preparation.data_classes.points_per_line import TransectLinesAtPoint


def create_one_side_of_transect(point, theta, line_length: float, rotation_angle: float) -> LineString:
    bearing = math.radians(theta + rotation_angle)
    x = point.x + line_length * math.cos(bearing)
    y = point.y + line_length * math.sin(bearing)
    return LineString(((point.x, point.y), (x, y)))


def calculate_transects(
    points_to_calculate_transects_on: gpd.GeoDataFrame, line_length: int
) -> list[TransectLinesAtPoint]:
    points_to_calculate_transects_on["theta_angle"] = numpy.nan
    for i, (first_point, second_point) in enumerate(pairwise(points_to_calculate_transects_on.geometry)):
        points_to_calculate_transects_on.loc[i, "theta_angle"] = angle_between_two_points(first_point, second_point)

    transect_lines_and_points = []
    for i, (index, row) in enumerate(points_to_calculate_transects_on.iterrows()):
        right_line = create_one_side_of_transect(
            row.geometry, theta=row["theta_angle"], line_length=line_length, rotation_angle=90
        )
        left_line = create_one_side_of_transect(
            row.geometry, theta=row["theta_angle"], line_length=line_length, rotation_angle=-90
        )
        transect_lines_and_points.append(
            TransectLinesAtPoint(row.geometry, right_line, left_line, i, row["z_interpolated"])
        )

    return transect_lines_and_points


def cut_line_at_points(line: LineString, points: Sequence[Point]) -> list[LineString]:
    # First coords of line
    coords = list(line.coords)

    # Keep list coords where to cut (cuts = 1)
    cuts = [0] * len(coords)
    cuts[0] = 1
    cuts[-1] = 1

    # Add the coords from the points
    coords += [list(p.coords)[0] for p in points]
    cuts += [1] * len(points)

    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]
    coords = [p for (d, p) in sorted(zip(dists, coords))]
    cuts = [p for (d, p) in sorted(zip(dists, cuts))]

    lines = []

    for i in range(len(coords) - 1):
        if cuts[i] == 1:
            # find next element in cuts == 1 starting from index i + 1
            j = cuts.index(1, i + 1)
            lines.append(LineString(coords[i : j + 1]))

    return lines


def trim_intersecting_parts_of_transects(
    transects_per_point_on_center_line: list[TransectLinesAtPoint],
) -> list[TransectLinesAtPoint]:
    trimmed_transects_per_point_on_center_line: dict[int, TransectLinesAtPoint] = {
        transects_with_point.transect_number: transects_with_point
        for transects_with_point in transects_per_point_on_center_line
    }
    for first_transect, second_transect in combinations(transects_per_point_on_center_line, 2):
        first_transect: TransectLinesAtPoint
        second_transect: TransectLinesAtPoint
        intersection_result = first_transect.left_line.intersection(second_transect.left_line)
        lines_do_intersect = isinstance(intersection_result, Point)
        if lines_do_intersect:
            first_trimmed_lines = cut_line_at_points(first_transect.left_line, [intersection_result])
            first_trimmed_line = get_line_that_originates_at_center_point(first_transect, first_trimmed_lines)
            update_transect_left_line_if_its_shorter(
                first_transect, first_trimmed_line, trimmed_transects_per_point_on_center_line
            )
            second_trimmed_lines = cut_line_at_points(second_transect.left_line, [intersection_result])
            second_trimmed_line = get_line_that_originates_at_center_point(second_transect, second_trimmed_lines)
            update_transect_left_line_if_its_shorter(
                second_transect, second_trimmed_line, trimmed_transects_per_point_on_center_line
            )
        intersection_result = first_transect.right_line.intersection(second_transect.right_line)
        lines_do_intersect = isinstance(intersection_result, Point)
        if lines_do_intersect:
            first_trimmed_lines = cut_line_at_points(first_transect.right_line, [intersection_result])
            first_trimmed_line = get_line_that_originates_at_center_point(first_transect, first_trimmed_lines)
            update_transect_right_line_if_its_shorter(
                first_transect, first_trimmed_line, trimmed_transects_per_point_on_center_line
            )
            second_trimmed_lines = cut_line_at_points(second_transect.right_line, [intersection_result])
            second_trimmed_line = get_line_that_originates_at_center_point(second_transect, second_trimmed_lines)
            update_transect_right_line_if_its_shorter(
                second_transect, second_trimmed_line, trimmed_transects_per_point_on_center_line
            )

    return list(trimmed_transects_per_point_on_center_line.values())


def get_line_that_originates_at_center_point(
    transect: TransectLinesAtPoint, trimmed_lines: Iterable[LineString]
) -> LineString:
    matching_line = None
    for line in trimmed_lines:
        if transect.point.intersects(line):
            matching_line = line
            break
    assert matching_line is not None
    return matching_line


def update_transect_left_line_if_its_shorter(
    transect: TransectLinesAtPoint,
    trimmed_line: LineString,
    trimmed_transects_per_point_on_center_line: dict[int, TransectLinesAtPoint],
):
    first_transect_lines_with_point = trimmed_transects_per_point_on_center_line[transect.transect_number]
    current_trimmed_line = first_transect_lines_with_point.left_line
    if current_trimmed_line.length > trimmed_line.length:
        trimmed_transects_per_point_on_center_line[transect.transect_number] = replace(
            first_transect_lines_with_point, left_line=trimmed_line
        )


def update_transect_right_line_if_its_shorter(
    transect: TransectLinesAtPoint,
    trimmed_line: LineString,
    trimmed_transects_per_point_on_center_line: dict[int, TransectLinesAtPoint],
):
    first_transect_lines_with_point = trimmed_transects_per_point_on_center_line[transect.transect_number]
    current_trimmed_line = first_transect_lines_with_point.right_line
    if current_trimmed_line.length > trimmed_line.length:
        trimmed_transects_per_point_on_center_line[transect.transect_number] = replace(
            first_transect_lines_with_point, right_line=trimmed_line
        )


def sample_points_for_along_all_transects(
    transects_per_center_line: list[TransectLinesAtPoint], sampling_distance: float
) -> gpd.GeoDataFrame:
    all_points = gpd.GeoDataFrame()
    for transect in transects_per_center_line:
        left_samples = sample_points_along_line(gpd.GeoDataFrame({"geometry": [transect.left_line]}), sampling_distance)
        right_samples = sample_points_along_line(
            gpd.GeoDataFrame({"geometry": [transect.right_line]}), sampling_distance
        )
        combined = left_samples.append(right_samples, ignore_index=True)
        combined["z_interpolated"] = transect.elevation
        all_points = all_points.append(combined)
    return all_points
