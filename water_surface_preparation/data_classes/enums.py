from enum import Enum


class ShoreTypes(Enum):
    open_shore = 1
    covered = 2
    around_vegetation = 3


class Scenario(Enum):
    af_2021 = "AF_2021"
    af_2020 = "AF_2020"
    bf_2020 = "BF_2020"
