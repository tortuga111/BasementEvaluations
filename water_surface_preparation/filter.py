import geopandas as gpd


def filter_outliers_from_elevation_points(
    points_with_elevation: gpd.GeoDataFrame, buffer_distance: int, maximal_deviation: float
) -> gpd.GeoDataFrame:
    do_keep_this_row = []
    for i, point in points_with_elevation.iterrows():
        buffer = point.geometry.buffer(buffer_distance)
        points_in_buffer = gpd.GeoDataFrame(
            geometry=points_with_elevation.intersection(buffer), crs=points_with_elevation.crs
        )
        median_elevation = points_with_elevation[~points_in_buffer.is_empty]["z_raster"].median()
        is_not_an_outlier = -maximal_deviation < (median_elevation - point["z_raster"]) < maximal_deviation
        do_keep_this_row.append(True if is_not_an_outlier else False)
    print(f"filtering removed {sum(not row for row in do_keep_this_row)} of {len(do_keep_this_row)} points")
    filtered = points_with_elevation[do_keep_this_row]
    filtered.reset_index(drop=True, inplace=True)
    assert filtered.__len__() == sum(do_keep_this_row)
    return filtered
