from statsmodels import api as sm

from water_surface_preparation.data_classes.points_per_line import (
    OrderedProjectedPointsPerCenterLine,
    ProcessedPointsPerCenterLine,
)


def apply_rolling_window_smoothing(
    projected_points: OrderedProjectedPointsPerCenterLine,
) -> ProcessedPointsPerCenterLine:
    rolling_mean = projected_points.projected_points["z_raster"].rolling(window=20, min_periods=1, center=True).mean()
    projected_points.projected_points["z_smooth"] = rolling_mean.values
    return ProcessedPointsPerCenterLine(projected_points.projected_points, projected_points.center_line)


def smooth_elevations_along_line(ordered_projected_points, frac):
    ordered_projected_points.projected_points["z_smooth"] = sm.nonparametric.lowess(
        ordered_projected_points.projected_points["z_raster"].values,
        ordered_projected_points.projected_points["distance"].values,
        frac=frac,
    )[:, 1]
    return ordered_projected_points
