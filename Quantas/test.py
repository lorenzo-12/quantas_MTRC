import pathlib 
import os 

TOPOLOGIES_DIR = pathlib.Path(__file__).parent / "quantas" / "topologies"
RESULTS_DIR = pathlib.Path(__file__).parent / "results"
SCRIPTS_DIR = pathlib.Path(__file__).parent / "scripts"


BASE_SCRIPT = """
#!/bin/bash

#OAR -l { host in ('big16','big17','big18', 'big19', 'big20')}/nodes=1/core=48,walltime=1000:0:0
#OAR -O server_output/edge_remover_%jobid%.stdout
#OAR -E server_output/edge_remover_%jobid%.stderr

source /etc/profile.d/modules.sh                # Shell initialization to use module
module purge                                                    # Environment cleanup
module load python/anaconda3                    # Loading of anaconda 3 module

conda activate quantas
""".strip()


def get_topology_files():
    return [f for f in TOPOLOGIES_DIR.iterdir() if f.is_file() and f.suffix == ".json"]

def get_results_files(topology_name):
    dir_path = RESULTS_DIR / topology_name
    return [f for f in dir_path.iterdir() if f.is_file() and f.suffix == ".json"]

def get_script_files():
    return [f for f in SCRIPTS_DIR.iterdir() if f.is_file() and f.suffix == ".sh"]

def generate_scripts_files():
    
    x = get_topology_files()
    for f in x:
        text = BASE_SCRIPT + f"\nmake run INPUTFILE=quantas/topologies/{f.name}"
        with open(SCRIPTS_DIR / f"{f.stem}.sh", "w") as script_file:
            script_file.write(text)


x = get_topology_files()
for f in x:
    text = open(f, "r").read()
    text = text.replace("results/edge_remover/100", "results/edge_remover_100")
    text = text.replace("results/random_regular/100", "results/random_regular_100")
    text = text.replace("results/erdos_renyi/100", "results/erdos_renyi_100")
    with open(f, "w") as topology_file:
        topology_file.write(text)
    
