import pathlib
import argparse
import json
import subprocess
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument(
    "--n",
    type=int,
    default=100,
    help="Run only topologies whose name contains n{n}",
)
args = parser.parse_args()

print(f"Running script with n={args.n}...")

TOPOLOGIES_DIR = pathlib.Path(__file__).parent / "quantas" / "topologies"
RESULTS_DIR = pathlib.Path(__file__).parent / "results"
SCRIPTS_DIR = pathlib.Path(__file__).parent / "scripts"


def get_topology_files():
    return [f for f in TOPOLOGIES_DIR.iterdir() if f.is_file() and f.suffix == ".json"]

def get_topology_runned():
    js_file = "experiment_runned.json"
    with open(js_file, "r", encoding="utf-8") as file_handle:
        experiment_runned = json.load(file_handle)
    return experiment_runned
    
def get_corresponding_script_file(result_file):
    tmp = ""
    if "both" in result_file.stem:
        tmp = result_file.stem.split("_both")[0]
    if "dolev" in result_file.stem:
        tmp = result_file.stem.split("_dolev")[0]
    
    x = tmp.split("_")
    script_file = f"{x[0]}_{x[1]}_n{x[2]}_k{x[3]}_t{x[4]}"
    return script_file

def run_scripts():
    topology_files = get_topology_files()
    topology_already_runned = get_topology_runned()
    
    topology_files.sort(key=lambda f: f.stem)
    
    for topology_file in topology_files:
        if f"n{args.n}" not in topology_file.stem:
            continue
        
        if topology_file.name in topology_already_runned:
            print(f"----{topology_file.name}")
            continue
        
        print(f"Running topology {topology_file.name}...")
        try:
            subprocess.run(
                ["make", "run", f"INPUTFILE=quantas/topologies/{topology_file.name}"],
                check=True,
            )
            subprocess.run(
                [sys.executable, "update_list.py", topology_file.name],
                check=True,
            )
        except KeyboardInterrupt:
            print("\nInterrupted by user. Stopping execution.")
            sys.exit(130)
    
        
    
run_scripts()
