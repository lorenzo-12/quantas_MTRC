import pathlib 
import os 
from time import sleep

TOPOLOGIES_DIR = pathlib.Path(__file__).parent / "quantas" / "topologies"
RESULTS_DIR = pathlib.Path(__file__).parent / "results"
SCRIPTS_DIR = pathlib.Path(__file__).parent / "scripts"


BASE_SCRIPT = """
#!/bin/bash

#OAR -n <job_name>
#OAR -l { host in ('big16','big17','big18', 'big19', 'big20', 'tall1', 'tall2', 'tall3', 'tall4', 'tall5', 'tall6', 'tall7', 'tall8', 'tall9', 'tall10', 'tall11', 'tall12', 'tall13', 'tall14', 'tall15', 'tall16', 'tall17', 'tall18', 'tall19', 'tall20')}/nodes=1/core=48,walltime=1000:0:0
#OAR -O server_output/%jobid%.stdout
#OAR -E server_output/%jobid%.stderr

source /etc/profile.d/modules.sh                # Shell initialization to use module

""".strip()


def get_topology_files():
    return [f for f in TOPOLOGIES_DIR.iterdir() if f.is_file() and f.suffix == ".json"]

def get_results_files():
    return [f for f in RESULTS_DIR.iterdir() if f.is_file() and f.suffix == ".json"]

def get_script_files():
    return [f for f in SCRIPTS_DIR.iterdir() if f.is_file() and f.suffix == ".sh" and f.stem != "script"]

def generate_scripts_files():
    
    x = get_topology_files()
    for f in x:
        text = BASE_SCRIPT + f"\nmake run INPUTFILE=quantas/topologies/{f.name}"
        text = text.replace("<job_name>", f.stem)
        text = text.replace("%jobid%.stdout", f"{f.stem}.stdout")
        text = text.replace("%jobid%.stderr", f"{f.stem}.stderr")
        script_path = SCRIPTS_DIR / f"{f.stem}.sh"
        with open(script_path, "w") as script_file:
            script_file.write(text)
    
    # run in the terminal
    os.system("chmod +x /home/difilippo/quantas_MTRC/Quantas/scripts/*.sh")


def get_corresponding_script_file(result_file):
    tmp = ""
    if "both" in result_file.stem:
        tmp = result_file.stem.split("_both")[0]
    if "dolev" in result_file.stem:
        tmp = result_file.stem.split("_dolev")[0]
    
    x = tmp.split("_")
    script_file = f"{x[0]}_{x[1]}_n{x[2]}_k{x[3]}_t{x[4]}"
    return script_file
    


threshold = 10
def run_scripts():
    scripts_files = get_script_files()
    scripts_files = [f for f in scripts_files if "100" not in f.stem]
    results_files = set()
    
    for f in get_results_files():
        script_file = get_corresponding_script_file(f)
        results_files.add(script_file)
    
    ord_results_files = sorted(results_files)
    print(f"SCRIPT RUNNED/RUNNING ({len(ord_results_files)}/{len(scripts_files)}):")
    for f in ord_results_files:
        print(f"  - {f}")
    print("\n\n")
    
    cnt = 0
    for f in scripts_files:
        if f.stem not in results_files:
            print(f"Script {"scripts/" + str(f.name)} needs to be run.")
            script_file = "scripts/" + str(f.name)
            script_file = script_file.replace("<job_name>", f.stem)
    
            os.system(f"oarsub -S {script_file}")
            cnt += 1
            sleep(2)  # Sleep for a short time to avoid overwhelming the cluster with too many submissions at once
            if cnt >= threshold:
                print(f"Submitted {threshold} scripts, stopping to avoid overloading the cluster.")
                break
            

start = 1282482
end = 1282486
def stop_runs(start, end):
    for i in range(start, end + 1):
        os.system(f"oardel {i}")


#generate_scripts_files()
#run_scripts()
#stop_runs(start, end)
