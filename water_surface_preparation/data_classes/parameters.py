from dataclasses import dataclass

from water_surface_preparation.data_classes.enums import Scenario


@dataclass(frozen=True)
class ParametersToFilterSamplingPoints:
    buffer_distance: int
    maximal_deviation: float


@dataclass(frozen=True)
class ParametersToAssignElevationToPoints:
    buffer_distance: int


@dataclass(frozen=True)
class ParametersForOneProcess:
    demanded_scenario: Scenario
    sampling_distance: int
    buffer_distance: int
    line_length: int
    frac: float
    parameters_to_filter_sampling_points: ParametersToFilterSamplingPoints
    parameters_to_assign_elevation_to_points: ParametersToAssignElevationToPoints
