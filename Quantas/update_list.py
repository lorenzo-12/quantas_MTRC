import argparse
import json

js_file = "experiment_runned.json"

parser = argparse.ArgumentParser()
parser.add_argument(
    "experiment_file",
    nargs="?",
    default="exp_1.sh",
    help="Path to the JSON file to load",
)
args = parser.parse_args()

with open(js_file, "r", encoding="utf-8") as file_handle:
    experiment_runned = json.load(file_handle)
    experiment_runned.append(args.experiment_file)
with open(js_file, "w", encoding="utf-8") as file_handle:
    json.dump(experiment_runned, file_handle, indent=4)






