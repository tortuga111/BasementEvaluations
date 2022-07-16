import os.path
import time
from abc import ABC
from collections import deque
from dataclasses import dataclass
from typing import Deque, Type


@dataclass(frozen=True)
class BaseLogEntry(ABC):
    experiment_id: str


@dataclass(init=False)
class CSVLogger:
    _LOG_FILE_FOLDER = r".\.logs"
    _type_of_message_to_log: Type[BaseLogEntry]
    _start_time: float
    _logs: Deque[BaseLogEntry]

    def __init__(self, type_of_message_to_log: Type[BaseLogEntry]):
        self._type_of_message_to_log = type_of_message_to_log
        self._start_time = time.time()
        self._logs = deque([])

    def add_entry_to_log(self, log_entry: BaseLogEntry) -> None:
        if not type(log_entry) is self._type_of_message_to_log:
            raise AssertionError(f"{log_entry} is not of same type as {self._type_of_message_to_log}")
        self._logs.append(log_entry)

    def write_logs_as_csv_to_file(self, file_name: str) -> str:
        path = os.path.join(self._LOG_FILE_FOLDER, file_name)
        sep = ";"
        self._make_folder_for_logs_if_needed()
        with open(path, "w") as file_to_write_to:
            self.__create_csv_header(file_to_write_to, sep)
            self.__add_rows(file_to_write_to, sep)
        return path

    def __add_rows(self, file_to_write_to, sep):
        file_to_write_to.writelines(
            f"{sep.join(str(value) for value in log.__dict__.values())}\n" for log in self._logs
        )

    def __create_csv_header(self, file_to_write_to, sep):
        file_to_write_to.write(
            f"{sep.join((key for key in self._type_of_message_to_log.__dict__['__dataclass_fields__'].keys()))}\n"
        )

    @classmethod
    def _make_folder_for_logs_if_needed(cls):
        if not os.path.exists(cls._LOG_FILE_FOLDER):
            os.mkdir(cls._LOG_FILE_FOLDER)


@dataclass(frozen=True)
class GoodnessOfFitForInitialVelocity(BaseLogEntry):
    v_obs_mean: float
    v_obs_std: float
    v_obs_min: float
    v_obs_max: float
    v_sim_mean: float
    v_sim_std: float
    v_sim_min: float
    v_sim_max: float
    v_mean_error: float
    v_mean_absolute_error: float
    v_root_mean_square_error: float
    v_percent_bias: float
    v_nash_sutcliffe_efficiency: float
    v_index_of_agreement: float


@dataclass(frozen=True)
class GoodnessOfFitForInitialBottomElevation(BaseLogEntry):
    bot_ele_obs_mean: float
    bot_ele_obs_std: float
    bot_ele_obs_min: float
    bot_ele_obs_max: float
    bot_ele_sim_mean: float
    bot_ele_sim_std: float
    bot_ele_min: float
    bot_ele_max: float
    bot_ele_mean_error: float
    bot_ele_mean_absolute_error: float
    bot_ele_root_mean_square_error: float
    bot_ele_percent_bias: float
    bot_ele_nash_sutcliffe_efficiency: float
    bot_ele_index_of_agreement: float


@dataclass(frozen=True)
class GoodnessOfFitForInitialWaterDepth(BaseLogEntry):
    wd_obs_mean: float
    wd_obs_std: float
    wd_obs_min: float
    wd_obs_max: float
    wd_sim_mean: float
    wd_sim_std: float
    wd_sim_min: float
    wd_sim_max: float
    wd_mean_error: float
    wd_mean_absolute_error: float
    wd_root_mean_square_error: float
    wd_percent_bias: float
    wd_nash_sutcliffe_efficiency: float
    wd_index_of_agreement: float


@dataclass(frozen=True)
class GoodnessOfFitFor3dEvaluation(BaseLogEntry):
    polygon_name: str
    area_polygon: float
    ratio_of_eroded_area_dod: float
    ratio_of_deposited_area_dod: float
    ratio_of_eroded_area_sim: float
    ratio_of_deposited_area_sim: float
    ratio_of_identical_change: float
    ratio_of_different_change: float
    eroded_volume_sim: float
    deposited_volume_sim: float
    eroded_volume_dod: float
    deposited_volume_dod: float
    eroded_volume_absolute_error: float
    deposited_volume_absolute_error: float
    deposited_volume_absolute_error: float
    eroded_volume_per_area_sim: float
    deposited_volume_per_area_sim: float
    eroded_volume_per_area_dod: float
    deposited_volume_per_area_dod: float
    eroded_volume_per_area_abs_error: float
    deposited_volume_per_area_abs_error: float


@dataclass(frozen=True)
class ShearStress(BaseLogEntry):
    time_step: float
    discharge: float
    wetted_area: float
    abs_area_tau_more_than_10Nm: float
    abs_area_tau_more_than_20Nm: float
    abs_area_tau_more_than_30Nm: float
    abs_area_tau_more_than_40Nm: float
    abs_area_tau_more_than_50Nm: float
    abs_area_tau_more_than_60Nm: float
    abs_area_tau_more_than_70Nm: float
    abs_area_tau_more_than_80Nm: float
    abs_area_tau_more_than_90Nm: float
    abs_area_tau_more_than_D90: float
    abs_area_critical_shield_stress_chezy: float
    rel_area_critical_shield_stress_chezy: float
    area_guenter_criterion_chezy: float
    rel_area_guenter_criterion_chezy: float


@dataclass(frozen=True)
class ScenarioEvaluationHmid(BaseLogEntry):
    time_step: float
    wetted_area: float
    water_depth_variability: float
    flow_velocity_variability: float
    hydro_morphological_index_of_diversity: float
