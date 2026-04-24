import os 
import pathlib


TOPOLOGIES_DIR = pathlib.Path(__file__).parent / "quantas" / "topologies"
RESULTS_DIR = pathlib.Path(__file__).parent / "results"
SCRIPTS_DIR = pathlib.Path(__file__).parent / "scripts"


def get_topology_files():
    return [f for f in TOPOLOGIES_DIR.iterdir() if f.is_file() and f.suffix == ".json"]

def get_results_files():
    return [f for f in RESULTS_DIR.iterdir() if f.is_file() and f.suffix == ".json"]
    
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
    results_files = get_results_files()
    topology_already_runned = set()
    
    """ for result_file in results_files:
        script_file = get_corresponding_script_file(result_file)
        topology_already_runned.add(script_file) """
    
    test_to_run = sorted(topology_files, key=lambda x: x.stem)
    
    for topology_file in test_to_run:
        if "n100" not in topology_file.stem:
            continue 
        
        if topology_file.stem not in topology_already_runned:
            print(f"Running topology {topology_file.name}...")
            os.system(f"make run INPUTFILE=quantas/topologies/{topology_file.name}")
            break
        else:
            print(f"Topology {topology_file.stem} already runned, skipping...")
            continue
    
    
run_scripts()

