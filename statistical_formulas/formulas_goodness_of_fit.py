import math

import geopandas as gpd
import numpy as np

from misc.dataclasses_for_evaluations import ColumnNamePair


def calculate_average_error(point_dataset: gpd.GeoDataFrame, colum_names: ColumnNamePair):
    return np.divide(
        sum(np.subtract(point_dataset[colum_names.simulated], point_dataset[colum_names.observed])), len(point_dataset)
    )


def calculate_mean_absolute_error(point_dataset: gpd.GeoDataFrame, column_names: ColumnNamePair):
    return np.divide(
        sum(abs(np.subtract(point_dataset[column_names.simulated], point_dataset[column_names.observed]))),
        len(point_dataset),
    )


def calculate_root_mean_square_error(point_dataset: gpd.GeoDataFrame, column_names: ColumnNamePair):
    return math.sqrt(
        np.divide(
            sum(np.square(np.subtract(point_dataset[column_names.simulated], point_dataset[column_names.observed]))),
            len(point_dataset),
        )
    )


def calculate_percent_bias(point_dataset: gpd.GeoDataFrame, column_names: ColumnNamePair):
    return np.multiply(
        100,
        (
            np.divide(
                np.subtract(
                    np.mean(point_dataset[column_names.simulated]), np.mean(point_dataset[column_names.observed])
                ),
                np.mean(point_dataset[column_names.observed]),
            )
        ),
    )


def calculate_nash_sutcliffe_efficiency(point_dataset: gpd.GeoDataFrame, column_names: ColumnNamePair):
    return 1 - np.divide(
        sum(np.square(np.subtract(point_dataset[column_names.simulated], point_dataset[column_names.observed]))),
        sum(
            np.square(np.subtract(point_dataset[column_names.observed], np.mean(point_dataset[column_names.observed])))
        ),
    )


def calculate_index_of_agreement(point_dataset: gpd.GeoDataFrame, column_names: ColumnNamePair):
    return 1 - np.divide(
        sum(np.square(np.subtract(point_dataset[column_names.simulated], point_dataset[column_names.observed]))),
        sum(
            np.square(
                abs(np.subtract(point_dataset[column_names.simulated], np.mean(point_dataset[column_names.observed])))
                + abs(np.subtract(point_dataset[column_names.observed], np.mean(point_dataset[column_names.observed]))),
            )
        ),
    )


def calculate_water_depth_variability(water_depth_point_variability: gpd.GeoDataFrame):
    return water_depth_point_variability.std() / water_depth_point_variability.mean() * 100


def calculate_hydromorphological_index_of_diversity(
    velocity_point_data_set: gpd.GeoDataFrame, water_depth_point_data_set: gpd.GeoDataFrame
):
    return np.multiply(
        ((1 + velocity_point_data_set.std() / velocity_point_data_set.mean()) ** 2),
        ((1 + water_depth_point_data_set.std() / water_depth_point_data_set.mean()) ** 2),
    )
