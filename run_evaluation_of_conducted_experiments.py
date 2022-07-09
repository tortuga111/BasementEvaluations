import dataclasses
import json
import os
import pickle
from collections import defaultdict
from typing import NamedTuple, Iterable, Sized

import geopandas as gpd
import matplotlib.colors
import matplotlib.pyplot as plt
import pandas as pd
from geopandas import GeoDataFrame
from tqdm import tqdm

from all_paths import PathsToJsonWithExperimentPath
from csv_logging.calculate_entries import (
    goodness_of_fit_for_bottom_elevation,
    goodness_of_fit_for_velocity,
    goodness_of_fit_for_water_depth,
    goodness_of_fit_for_three_d_analysis,
)
from csv_logging.csvlogger import (
    CSVLogger,
    GoodnessOfFitForInitialVelocity,
    GoodnessOfFitForInitialBottomElevation,
    GoodnessOfFitForInitialWaterDepth,
    GoodnessOfFitFor3dEvaluation,
    ShearStress,
    ScenarioEvaluationHmid,
)
from evaluation_runner.analysis_calibration.three_dimensional import (
    create_union_of_dod_and_simulated_dz_mesh,
    clip_mesh_with_polygons,
)
from evaluation_runner.profiles.evaluate_profiles import (
    create_histogram_with_mesh_values,
    evaluate_points_along_profiles,
    create_scatter_plot,
    create_scatter_plot_for_velocities,
)
from evaluation_runner.scenario_evaluation.evaluate_water_depth_change import (
    calculate_mean_de_watering_speed_over_time,
    DeWateringSpeedCalculationParameters,
)
from evaluation_runner.scenario_evaluation.final_scenario_evaluation_log_entries import (
    calculate_and_log_hmid_statistics,
)
from evaluation_runner.scenario_evaluation.shield_stress import (
    calculate_shear_stress_coefficients,
    ParametersForShearStressEvaluation,
    calculate_and_log_shear_stress_statistics,
    create_parameters_for_shear_stress,
    select_area_where_guenter_criterion_is_reached,
    select_area_where_guenter_criterion_is_reached_chezy,
    select_area_where_crit_shield_stress_is_reached,
    select_area_where_crit_shield_stress_is_reached_with_chezy,
)
from evaluation_runner.scenario_evaluation.visualizations_shear_stress import \
    another_function_that_will_sexually_embarrass_me
from extract_data.create_shape_files_from_simulation_results import process_h5_files_to_shape_files
from extract_data.summarising_mesh import (
    create_default_state_to_name_in_shape_file_mapping,
    create_mesh_with_before_and_after_flood_data,
    assign_requested_values_from_summarising_mesh_to_point,
    create_mesh_from_mapped_values,
    StateToNameInShapeFileMapping,
)
from profile_creation.containers import BeforeOrAfterFloodScenario
from script_for_profile_creation import create_paths
from utils.loading import load_data_with_crs_2056


def get_json_with_all_result_paths(path_to_all_experiments_to_evaluate: PathsToJsonWithExperimentPath) -> list[str]:
    with open(path_to_all_experiments_to_evaluate, "r") as json_file:
        return list(json.load(json_file))


def inclusive_range(start: int, stop: int, step: int) -> Iterable[int]:
    for i in range(start, stop, step):
        yield i
    yield stop


@dataclasses.dataclass(frozen=True)
class XDistanceMapper:
    _length_per_group: float
    _gap_between_groups: float
    _classes_per_group: int


def _map_material_index_to_name(index: int) -> str:
    if index == 1:
        return "water"
    if index == 5:
        return "water"
    if index == 8:
        return "water"
    if index == 2:
        return "gravel"
    if 3 <= index <= 4:
        return "vegetation"
    if 6 <= index <= 7:
        return "vegetation"
    raise NotImplementedError(index)


def the_plot_that_forces_me_to_wear_sexy_stuff(
    selection_where_flow_velocity_and_wd_are_too_small: GeoDataFrame, tau_bins: list[float]
) -> None:
    _length_per_group: float = 10
    _gap_between_groups: float = 2.5
    _classes_per_group: int = len(tau_bins)

    from plotly import graph_objects as go

    fig = go.Figure()

    selection_where_flow_velocity_and_wd_are_too_small[
        "material_name"
    ] = selection_where_flow_velocity_and_wd_are_too_small["material_index"].apply(_map_material_index_to_name)

    fig.update_layout(
        xaxis=dict(title_text="Discharge"),
        yaxis=dict(title_text="Area"),
        barmode="stack",
    )
    color_map = {"vegetation": "green", "water": "blue", "gravel": "grey"}

    selection_where_flow_velocity_and_wd_are_too_small["tau_chezy_bin"] = pd.cut(
        selection_where_flow_velocity_and_wd_are_too_small["tau_chezy"], retbins=True, bins=tau_bins
    )[0]
    outer_x_location = inner_x_location = 0
    x_tick_labels = []
    x_tick_location = []
    step_per_inner_bar = _length_per_group / _classes_per_group

    total_at_this_position = []
    for discharge, outer_group in selection_where_flow_velocity_and_wd_are_too_small.groupby("discharge"):
        outer_x_location += _gap_between_groups
        x_tick_labels.append(f"\n\n\n{discharge}")
        x_tick_location.append(outer_x_location + inner_x_location + step_per_inner_bar / 2)
        for tau_chezy_bin, inner_group in outer_group.groupby("tau_chezy_bin"):
            inner_x_location += step_per_inner_bar
            x_tick_labels.append(f"{tau_chezy_bin}")
            location = outer_x_location + inner_x_location
            x_tick_location.append(location)
            total_at_this_position.append((location, inner_group.area.sum()))
            for material_name, group in inner_group.groupby("material_name"):
                name = f"{discharge}_{tau_chezy_bin}_{material_name}"
                fig.add_trace(
                    go.Bar(
                        x=[location, outer_x_location],
                        y=[group.area.sum()],
                        name=name,
                        marker_color=color_map[material_name],
                        showlegend=False,
                        legendgroup=f"{material_name}",
                    )
                )

    summary = {
        tuple(name): group.area.sum()
        for name, group in selection_where_flow_velocity_and_wd_are_too_small.groupby(
            ["discharge", "tau_chezy_bin", "material_name"]
        )
    }
    pd.DataFrame(data=summary, index=[0]).to_csv("dump.csv", sep=";")

    fig.update_layout(xaxis=dict(ticktext=x_tick_labels, tickvals=x_tick_location, tickangle=-90))

    dummy_traces = [
        go.Scatter(x=[None], y=[None], name=material_name, mode="markers", marker=dict(symbol=1, color=color))
        for material_name, color in color_map.items()
    ]
    fig.add_traces(dummy_traces)
    fig.update_layout(legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))

    fig.add_trace(
        go.Scatter(
            x=[i[0] for i in total_at_this_position],
            y=[i[1] for i in total_at_this_position],
            mode="text",
            text=[str(round(i[1], 2)) for i in total_at_this_position],
            textposition="top center",
            showlegend=False,
        )
    )

    fig.show()


def evaluate_simulation_on_given_points(
    path_to_all_experiments_to_evaluate: PathsToJsonWithExperimentPath,
    evaluation_points: GeoDataFrame,
    path_to_mesh: str,
    flood_scenario: BeforeOrAfterFloodScenario,
    path_to_dod_as_polygon: str,
    paths_to_polygon_as_area_of_interest: tuple[str, ...],
    path_to_folder_containing_points_with_lines: str,
    simulation_time_in_seconds: int,
    evaluation_parameters_for_shear_stress: ParametersForShearStressEvaluation,
    sample_time_step_width: int,
):
    logger_hmid = CSVLogger(ScenarioEvaluationHmid)
    logger_shear_stress = CSVLogger(ShearStress)
    logger_goodness_of_fit_for_bottom_elevation = CSVLogger(GoodnessOfFitForInitialBottomElevation)
    logger_goodness_of_fit_for_water_depth = CSVLogger(GoodnessOfFitForInitialWaterDepth)
    logger_goodness_of_fit_for_velocity = CSVLogger(GoodnessOfFitForInitialVelocity)
    logger_goodness_of_fit_for_three_d_evaluation = CSVLogger(GoodnessOfFitFor3dEvaluation)

    logger_triple = GpsPointsLoggerTriple(
        logger_goodness_of_fit_for_velocity=logger_goodness_of_fit_for_velocity,
        logger_goodness_of_fit_for_water_depth=logger_goodness_of_fit_for_water_depth,
        logger_goodness_of_fit_for_bottom_elevation=logger_goodness_of_fit_for_bottom_elevation,
    )

    all_paths_to_experiment_results = get_json_with_all_result_paths(path_to_all_experiments_to_evaluate)
    before_flood_mapping = create_default_state_to_name_in_shape_file_mapping(0)
    after_flood_mapping = create_default_state_to_name_in_shape_file_mapping(simulation_time_in_seconds)
    time_stamps_to_evaluate_individually = list(
        inclusive_range(start=0, stop=simulation_time_in_seconds, step=sample_time_step_width)
    )

    for path in all_paths_to_experiment_results:
        experiment_id = os.path.split(path)[-1]
        resulting_geo_data_frames = process_h5_files_to_shape_files(
            path, path_to_mesh=path_to_mesh, time_step=sample_time_step_width, used_geomorphologic_module=False
        )

        if do_de_watering_speed_analysis := False:
            meshes_to_unify = []
            de_watering_parameters = DeWateringSpeedCalculationParameters(
                exclude_water_depth_above=1.0,
                exclude_water_depth_below=0.1,
                time_stamps_to_evaluate_change_on=time_stamps_to_evaluate_individually,
            )
            for time_stamp in tqdm(time_stamps_to_evaluate_individually):
                mapping_for_step = create_default_state_to_name_in_shape_file_mapping(time_stamp)
                mesh_for_this_time_step = create_mesh_from_mapped_values(resulting_geo_data_frames, mapping_for_step)
                meshes_to_unify.append(mesh_for_this_time_step)
            meshes_to_unify.reverse()
            mesh_with_all_time_steps = meshes_to_unify.pop()
            for mesh in tqdm(reversed(meshes_to_unify)):
                for column in filter(lambda x: x != "geometry", mesh.columns.values.tolist()):
                    mesh_with_all_time_steps[column] = mesh[column]
            mesh_with_all_time_steps = mesh_with_all_time_steps.copy()

            dewatering_mesh = calculate_mean_de_watering_speed_over_time(
                mesh_with_all_time_steps, de_watering_parameters
            )

            condition_dewatering_speed_very_big = dewatering_mesh["avg_cm/h"] < -30
            condition_dewatering_speed_big = (dewatering_mesh["avg_cm/h"] < -20) & (dewatering_mesh["avg_cm/h"] >= -30)
            condition_dewatering_speed_moderate = (dewatering_mesh["avg_cm/h"] < -10) & (
                dewatering_mesh["avg_cm/h"] >= -20
            )
            condition_dewatering_speed_small = (dewatering_mesh["avg_cm/h"] < 0) & (dewatering_mesh["avg_cm/h"] >= -10)

            dewatering_mesh["speed"] = None
            dewatering_mesh.loc[condition_dewatering_speed_small, "speed"] = "0 - 10"
            dewatering_mesh.loc[condition_dewatering_speed_moderate, "speed"] = "10.1 - 20"
            dewatering_mesh.loc[condition_dewatering_speed_big, "speed"] = "20.1 - 30"
            dewatering_mesh.loc[condition_dewatering_speed_very_big, "speed"] = "> 30"

            file_path = os.path.join("out", "dewatering_shape", experiment_id)
            if not os.path.exists(file_path):
                os.mkdir(file_path)

            area_per_dewatering_speed = {
                speed_level: group.area.sum() for speed_level, group in dewatering_mesh.groupby("speed")
            }
            area_per_dewatering_speed["experiment_id"] = experiment_id
            pd.DataFrame(index=[0], data=area_per_dewatering_speed).to_csv(
                os.path.join(file_path, "area_per_dewatering_speed.csv")
            )

            cmap = matplotlib.colors.ListedColormap(["#f0f9e8", "#bae4bc", "#7bccc4", "#2b8cbe"])

            dewatering_mesh.plot(column="speed", cmap=cmap, legend=True, missing_kwds={"color": "white"})
            file_name = f"dewatering_categorized.jpg"
            plt.savefig(file_path + file_name)

            # file_name = f"dewatering.shp"
            # dewatering_mesh.to_file(file_path + file_name)

        # evaluate some intermediate states without comparison:
        print(experiment_id)

        if do_individual_evaluations := True:
            _all_selections_to_concat = []
            for time_stamp in tqdm(time_stamps_to_evaluate_individually):
                mapping_for_step = create_default_state_to_name_in_shape_file_mapping(time_stamp)
                mesh_for_this_time_step = create_mesh_from_mapped_values(resulting_geo_data_frames, mapping_for_step)
                selection_where_flow_velocity_and_wd_are_too_small = calculate_shear_stress_coefficients(
                    mesh_for_this_time_step,
                    evaluation_parameters=evaluation_parameters_for_shear_stress,
                    state_to_name_in_shape_file_mapping=mapping_for_step,
                )
                _all_selections_to_concat.append(selection_where_flow_velocity_and_wd_are_too_small)
                _all_selections_to_concat[-1]["time_step"] = time_stamp
                # selection_where_flow_velocity_and_wd_are_too_small.to_file(
                # f"out\\shapes_shear_stress\\shear_stress{time_stamp}.gpkg", driver="GPKG"
                # )
                if log_shear_stress := False:
                    logger_shear_stress = calculate_and_log_shear_stress_statistics(
                        logger_shear_stress=logger_shear_stress,
                        time_step=time_stamp,
                        evaluation_parameters=evaluation_parameters_for_shear_stress,
                        experiment_id=experiment_id,
                        selection_where_wd_and_v_too_small=selection_where_flow_velocity_and_wd_are_too_small,
                    )

                    area_where_critical_shield_stress_is_reached = select_area_where_crit_shield_stress_is_reached(
                        selection_where_wd_and_v_too_small=selection_where_flow_velocity_and_wd_are_too_small,
                        evaluation_parameters=evaluation_parameters_for_shear_stress,
                    )

                    area_where_critical_shield_stress_is_reached_chezy = (
                        select_area_where_crit_shield_stress_is_reached_with_chezy(
                            selection_where_wd_and_v_too_small=selection_where_flow_velocity_and_wd_are_too_small,
                            evaluation_parameters=evaluation_parameters_for_shear_stress,
                        )
                    )

                    # area_where_critical_shield_stress_is_reached_chezy.plot()
                    # plt.savefig(f"out\\plots_shieldstress\\shield{time_stamp}_chezy.jpg")

                    area_where_guenter_criterion_is_reached = select_area_where_guenter_criterion_is_reached(
                        selection_where_wd_and_v_too_small=selection_where_flow_velocity_and_wd_are_too_small,
                        evaluation_parameters=evaluation_parameters_for_shear_stress,
                    )

                    area_where_guenter_criterion_is_reached_chezy = (
                        select_area_where_guenter_criterion_is_reached_chezy(
                            selection_where_wd_and_v_too_small=selection_where_flow_velocity_and_wd_are_too_small,
                            evaluation_parameters=evaluation_parameters_for_shear_stress,
                        )
                    )

                    # area_where_guenter_criterion_is_reached_chezy.plot()
                    # plt.savefig(f"out\\plots_shieldstress\\guenter{time_stamp}_chezy.jpg")

                if hmid := False:
                    logger_hmid = calculate_and_log_hmid_statistics(
                        logger_hmid=logger_hmid,
                        experiment_id=experiment_id,
                        evaluation_parameters=evaluation_parameters_for_shear_stress,
                        time_step=time_stamp,
                        mesh_with_simulation_state=mesh_for_this_time_step,
                        state_to_name_in_shape_file_mapping=mapping_for_step,
                    )

                    # selection_where_flow_velocity_and_wd_are_too_small.plot(column=f"fwd_{time_stamp}", cmap="Blues")
                    # plt.savefig("test.jpg")

            del _all_selections_to_concat[0]
            all_selections = gpd.GeoDataFrame(
                pd.concat(_all_selections_to_concat, axis=0, ignore_index=True), crs=_all_selections_to_concat[0].crs
            )
            all_selections["discharge"] = all_selections["time_step"]*30/8100
            another_function_that_will_sexually_embarrass_me(all_selections)
            the_plot_that_forces_me_to_wear_sexy_stuff(
                all_selections.drop(
                    all_selections[~all_selections["discharge"].isin({60, 120, 240, 360, 480})].index
                ),
                [0, 26.6, 55, float("inf")],
            )

            write_log_for_shear_stress(logger_shear_stress, flood_scenario=flood_scenario)
            write_log_for_hmid(logger_hmid, flood_scenario=flood_scenario)

        # compare initial and final state of simulation
        before_and_after_flood_mesh = create_mesh_with_before_and_after_flood_data(
            resulting_geo_data_frames,
            before_flood_mapping=before_flood_mapping,
            after_flood_mapping=after_flood_mapping,
        )

        valid_mapping = derive_columns_to_lookup_from_flood_scenario(
            before_flood_mapping, after_flood_mapping, flood_scenario
        )

        if do_points := False:
            renamed_updated_gps_points = assign_requested_values_from_summarising_mesh_to_point(
                columns_to_lookup=[pair.final_name for pair in valid_mapping],
                mesh_with_all_results=before_and_after_flood_mesh,
                points=evaluation_points.copy(deep=True),
            )
            renamed_updated_gps_points.to_file(f"out\\profiles\\gps_points_{experiment_id}.gpkg", driver="GPKG")

            logger_triple = calculate_and_log_statistics_for_gps_points(
                renamed_updated_gps_points,
                logger_triple,
                experiment_id=experiment_id,
                flood_scenario=flood_scenario,
                mapping=valid_mapping,
            )

            write_logs_for_gps_points(
                logger_triple,
                flood_scenario=flood_scenario,
            )

        if do_profiles := False:
            evaluate_points_along_profiles(
                mesh_with_all_results=before_and_after_flood_mesh,
                flood_scenario=flood_scenario,
                path_to_folder_containing_points_with_line=path_to_folder_containing_points_with_lines,
                colum_name_mapping=valid_mapping,
                experiment_id=experiment_id,
            )

        if do_polygons := False:
            union_of_dod_and_simulated_dz_mesh = create_union_of_dod_and_simulated_dz_mesh(
                path_to_dod_as_polygon=path_to_dod_as_polygon,
                mesh_with_all_results=before_and_after_flood_mesh,
            )

            # union_of_dod_and_simulated_dz_mesh.to_file(f"out\\polygons\\{experiment_id}.gpkg", driver="GPKG")

            all_polygons = dict()
            for polygon_path in tqdm(paths_to_polygon_as_area_of_interest):
                masking_polygons_for_evaluation = load_data_with_crs_2056(polygon_path)
                polygon_name = os.path.split(polygon_path)[-1].split(".")[0]
                clipped_mesh = clip_mesh_with_polygons(
                    union_of_dod_and_simulated_dz_mesh, masking_polygons_for_evaluation, experiment_id=experiment_id
                )

                logger_goodness_of_fit_for_three_d_evaluation = calculate_and_log_3d_statistics_for_polygons(
                    logger_goodness_of_fit_for_three_d_evaluation,
                    union_of_dod_and_simulated_dz_mesh=clipped_mesh,
                    experiment_id=experiment_id,
                    polygon_name=polygon_name,
                )
                all_polygons[polygon_name] = masking_polygons_for_evaluation

            if do_summary_of_all_polygons := False:
                all_masking_polygons = pd.concat(all_polygons.values())
                clipped_mesh = clip_mesh_with_polygons(
                    union_of_dod_and_simulated_dz_mesh, all_masking_polygons, experiment_id
                )
                clipped_mesh.to_file(f"out\\polygons\\polygons_{experiment_id}.gpkg", driver="GPKG")

                logger_goodness_of_fit_for_three_d_evaluation = calculate_and_log_3d_statistics_for_polygons(
                    logger_goodness_of_fit_for_three_d_evaluation,
                    union_of_dod_and_simulated_dz_mesh=clipped_mesh,
                    experiment_id=experiment_id,
                    polygon_name="-".join(all_polygons.keys()),
                )

            write_log_for_3d_evaluation(
                logger_goodness_of_fit_for_three_d_evaluation=logger_goodness_of_fit_for_three_d_evaluation,
                flood_scenario=flood_scenario,
            )


def derive_columns_to_lookup_from_flood_scenario(
    before_flood_mapping, after_flood_mapping, flood_scenario
) -> StateToNameInShapeFileMapping:
    if flood_scenario == BeforeOrAfterFloodScenario.bf_2020:
        return before_flood_mapping
    elif flood_scenario == BeforeOrAfterFloodScenario.af_2020:
        return after_flood_mapping
    else:
        raise NotImplementedError(f"{flood_scenario=} not available")


class GpsPointsLoggerTriple(NamedTuple):
    logger_goodness_of_fit_for_velocity: CSVLogger
    logger_goodness_of_fit_for_water_depth: CSVLogger
    logger_goodness_of_fit_for_bottom_elevation: CSVLogger


def calculate_and_log_3d_statistics_for_polygons(
    logger_goodness_of_fit_for_three_d_evaluation: CSVLogger,
    union_of_dod_and_simulated_dz_mesh: GeoDataFrame,
    experiment_id: str,
    polygon_name,
) -> CSVLogger:
    logger_goodness_of_fit_for_three_d_evaluation.add_entry_to_log(
        goodness_of_fit_for_three_d_analysis(union_of_dod_and_simulated_dz_mesh, experiment_id, polygon_name)
    )
    return logger_goodness_of_fit_for_three_d_evaluation


def calculate_and_log_statistics_for_gps_points(
    renamed_updated_gps_points: GeoDataFrame,
    logger_triple: GpsPointsLoggerTriple,
    experiment_id,
    flood_scenario,
    mapping: StateToNameInShapeFileMapping,
) -> GpsPointsLoggerTriple:
    water_depth_ = mapping.water_depth.final_name
    velocity_ = mapping.flow_velocity.final_name
    bottom_elevation_ = mapping.bottom_elevation.final_name

    renamed_updated_gps_points["wd_sim_gps"] = (
        renamed_updated_gps_points[water_depth_] - renamed_updated_gps_points["WT_m_"]
    )
    gps_points_with_velocity: GeoDataFrame = (
        renamed_updated_gps_points.loc[renamed_updated_gps_points["Vel__m_s_"] > 0, :]
    ).copy(deep=True)
    gps_points_with_velocity["v_sim_gps"] = gps_points_with_velocity[velocity_] - gps_points_with_velocity["Vel__m_s_"]

    create_histogram_with_mesh_values(
        renamed_updated_gps_points, "wd_sim_gps", flood_scenario=flood_scenario, experiment_id=experiment_id
    )
    create_histogram_with_mesh_values(
        gps_points_with_velocity, "v_sim_gps", flood_scenario=flood_scenario, experiment_id=experiment_id
    )

    filename = f"out\\gps_points_calibration\\gps_pts_calibration_{experiment_id}.pkl"
    with open(filename, "wb") as dump_file:
        pickle.dump(renamed_updated_gps_points, dump_file)

    create_scatter_plot(
        renamed_updated_gps_points,
        column_to_make_scatter_from_sim=water_depth_,
        flood_scenario=flood_scenario,
        experiment_id=experiment_id,
        column_to_make_scatter_from_obs="WT_m_",
    )

    create_scatter_plot_for_velocities(
        gps_points_with_velocity,
        column_to_make_scatter_from_sim=velocity_,
        flood_scenario=flood_scenario,
        experiment_id=experiment_id,
        column_to_make_scatter_from_obs="Vel__m_s_",
    )

    logger_triple.logger_goodness_of_fit_for_water_depth.add_entry_to_log(
        goodness_of_fit_for_water_depth(
            renamed_updated_gps_points, experiment_id=experiment_id, water_depth_name=water_depth_
        )
    )
    logger_triple.logger_goodness_of_fit_for_velocity.add_entry_to_log(
        goodness_of_fit_for_velocity(gps_points_with_velocity, experiment_id=experiment_id, velocity_name=velocity_)
    )
    logger_triple.logger_goodness_of_fit_for_bottom_elevation.add_entry_to_log(
        goodness_of_fit_for_bottom_elevation(
            renamed_updated_gps_points, experiment_id=experiment_id, bottom_elevation_name=bottom_elevation_
        )
    )
    return logger_triple


def write_logs_for_gps_points(
    logger_triple: GpsPointsLoggerTriple,
    flood_scenario: BeforeOrAfterFloodScenario,
) -> None:
    logger_triple.logger_goodness_of_fit_for_velocity.write_logs_as_csv_to_file(
        f"log_goodness_of_fit_{flood_scenario}_velocities.csv"
    )
    logger_triple.logger_goodness_of_fit_for_water_depth.write_logs_as_csv_to_file(
        f"log_goodness_of_fit_{flood_scenario}_water_depths.csv"
    )
    logger_triple.logger_goodness_of_fit_for_bottom_elevation.write_logs_as_csv_to_file(
        f"log_goodness_of_fit_{flood_scenario}_bottom_ele.csv"
    )


def write_log_for_3d_evaluation(
    logger_goodness_of_fit_for_three_d_evaluation: CSVLogger, flood_scenario: BeforeOrAfterFloodScenario
) -> None:
    logger_goodness_of_fit_for_three_d_evaluation.write_logs_as_csv_to_file(
        f"log_three_d_statistics_{flood_scenario}.csv"
    )


def write_log_for_shear_stress(logger_shear_stress: CSVLogger, flood_scenario: BeforeOrAfterFloodScenario) -> None:
    logger_shear_stress.write_logs_as_csv_to_file("log_shear_stress_fine_mesh.csv")


def write_log_for_hmid(logger_hmid: CSVLogger, flood_scenario: BeforeOrAfterFloodScenario) -> None:
    logger_hmid.write_logs_as_csv_to_file("log_hmid_input_01_fine_mesh.csv")


def main():
    flood_scenario = BeforeOrAfterFloodScenario.af_2020
    simulation_time_in_seconds = 243000
    sample_time_step_width = 8100

    paths_to_json_with_experiment_paths = PathsToJsonWithExperimentPath.stepwise_experiments_mesh2

    path_to_gps_points = create_paths(flood_scenario).path_to_gps_points
    # old:path_to_mesh = r"C:\Users\nflue\Documents\Masterarbeit\02_Data\04_Model_220309\04_Model\01_input_data_old\BF2020_Mesh\new_mesh_all_inputs\bathymetry_and_mesh_BF2020_computational-mesh.2dm"
    # path_to_mesh = r"C:\Users\nflue\Documents\Masterarbeit\02_Data\04_Model_220511\04_Model\01_input_data\BF2020_Mesh\new_mesh_all_inputs\Project1_computational-mesh.2dm"
    path_to_mesh = r"C:\Users\nflue\Documents\Masterarbeit\02_Data\04_Model_220620\04_Model\01_input_data\BF2020_Mesh\new_mesh_finer_01\Project1_computational-mesh.2dm"

    paths_to_polygon_as_area_of_interest = (
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\1.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\2.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\3.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\4.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\5.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\6.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\7.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\8.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\9.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\10.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\11.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\12.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\13.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\14.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\15.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\16.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\17.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\18.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\19.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\20.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\21.shp",
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\05_evaluation\\areas_to_compare_dod_bf_and_af\\22.shp",
    )
    path_to_dod_as_polygon = (
        "C:\\Users\\nflue\\Documents\\Masterarbeit\\02_Data\\03_Bathymetry\\DoDs\\dod_v2\\dod_as_polygon.shp"
    )
    path_to_folder_containing_points_with_lines = "C:\\Users\\nflue\\Documents\\Masterarbeit\\03_Projects\\MasterThesis\\BasementPreparation\\river_profiles_from_bathymetry"

    evaluation_parameters_for_shear_stress = create_parameters_for_shear_stress()

    evaluate_simulation_on_given_points(
        path_to_all_experiments_to_evaluate=paths_to_json_with_experiment_paths,
        evaluation_points=load_data_with_crs_2056(path_to_gps_points),
        path_to_mesh=path_to_mesh,
        flood_scenario=flood_scenario,
        paths_to_polygon_as_area_of_interest=paths_to_polygon_as_area_of_interest,
        path_to_dod_as_polygon=path_to_dod_as_polygon,
        path_to_folder_containing_points_with_lines=path_to_folder_containing_points_with_lines,
        simulation_time_in_seconds=simulation_time_in_seconds,
        evaluation_parameters_for_shear_stress=evaluation_parameters_for_shear_stress,
        sample_time_step_width=sample_time_step_width,
    )


if __name__ == "__main__":
    main()
