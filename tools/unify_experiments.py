import json
import os

from helpers.helpers import change_back_to_original_wd_afterwards


def write_all_paths_to_a_json(path: str, json_file_name: str) -> None:
    with change_back_to_original_wd_afterwards(path):
        all_paths = [os.path.abspath(path) for path in os.listdir(path) if os.path.isdir(path)]
        with open(json_file_name, "w") as json_file:
            json.dump(all_paths, json_file, indent=True)


def main():
    path_to_experiment_root_folder = (
        r"C:\Users\nflue\Desktop\experiments\experiments_old_mesh_batch1\runs_with_kst30_and_35_and_grain0.05_and_0.082"
    )
    write_all_paths_to_a_json(path_to_experiment_root_folder, "paths_to_experiments.json")


if __name__ == "__main__":
    main()