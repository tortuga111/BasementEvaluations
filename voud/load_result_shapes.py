from extract_data.create_shape_files_from_simulation_results import (
    SimulationResultsShapeFilePaths,
    SimulationResultsShapes,
)
from utils.loading import load_data_with_crs_2056


def load_data_from_simulations(paths: SimulationResultsShapeFilePaths) -> SimulationResultsShapes:
    return SimulationResultsShapes(
        bottom_elevation=load_data_with_crs_2056(paths.path_to_bottom_elevation),
        hydraulic_state=load_data_with_crs_2056(paths.path_to_hydraulic_state),
        flow_velocity=load_data_with_crs_2056(paths.path_to_flow_velocity),
        absolute_flow_velocity=load_data_with_crs_2056(paths.path_to_absolute_flow_velocity),
        chezy_coefficient=load_data_with_crs_2056(paths.path_to_chezy_coefficient),
    )
