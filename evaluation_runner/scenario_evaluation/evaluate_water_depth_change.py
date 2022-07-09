from typing import Sequence, List, NamedTuple

import geopandas as gpd
import numpy as np

from extract_data.summarising_mesh import create_default_state_to_name_in_shape_file_mapping
from utils import pairwise


def _create_column_names_for_water_depths(time_stamps_to_evaluate_change_on: Sequence[int]) -> list[str]:
    water_depth_column_name = []
    for time_stamp in time_stamps_to_evaluate_change_on:
        mapping = create_default_state_to_name_in_shape_file_mapping(time_stamp)
        water_depth_column_name.append(mapping.water_depth.final_name)
    return water_depth_column_name


class DeWateringSpeedCalculationParameters(NamedTuple):
    exclude_water_depth_above: float
    exclude_water_depth_below: float
    time_stamps_to_evaluate_change_on: Sequence[int]


def calculate_mean_de_watering_speed_over_time(
    data_frame_with_time_series_in_column: gpd.GeoDataFrame,
    parameters: DeWateringSpeedCalculationParameters,
) -> gpd.GeoDataFrame:
    df_to_return = gpd.GeoDataFrame(
        geometry=data_frame_with_time_series_in_column.geometry, crs=data_frame_with_time_series_in_column.crs
    )
    column_names = _create_column_names_for_water_depths(parameters.time_stamps_to_evaluate_change_on)
    delta_column_names = []
    time_deltas = (second - first for first, second in pairwise(parameters.time_stamps_to_evaluate_change_on))
    for (first_column_name, second_column_name), time_delta in zip(pairwise(column_names), time_deltas):
        delta = (
            data_frame_with_time_series_in_column[second_column_name]
            - data_frame_with_time_series_in_column[first_column_name]
        ) / time_delta
        initially_not_too_low = (
            data_frame_with_time_series_in_column[first_column_name] > parameters.exclude_water_depth_below
        )
        afterwards_not_too_high = (
            data_frame_with_time_series_in_column[second_column_name] < parameters.exclude_water_depth_above
        )
        is_decreasing = delta < 0
        all_conditions_satisfied = initially_not_too_low * afterwards_not_too_high * is_decreasing
        delta_column_name = f"{first_column_name}->{second_column_name}"
        df_to_return[delta_column_name] = np.where(all_conditions_satisfied, delta, np.nan)
        delta_column_names.append(delta_column_name)
    mapping = create_default_state_to_name_in_shape_file_mapping(parameters.time_stamps_to_evaluate_change_on[-1])

    last_evaluated_water_depth_ = mapping.water_depth.final_name
    condition_wd_too_small = data_frame_with_time_series_in_column[last_evaluated_water_depth_] <= 0.1

    df_to_return.where(condition_wd_too_small, np.nan, inplace=True, axis=0)

    df_to_return["avg_cm/h"] = (
        df_to_return[delta_column_names].mean(
            axis=1,
            skipna=True,
        )
        * 3600
        * 100
    )
    return df_to_return
