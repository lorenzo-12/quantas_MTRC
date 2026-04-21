import json 
import pathlib
import random

from numpy import ceil 

QUANTAS_TOPOLOGIES_DIR = pathlib.Path(__file__).parent / "quantas_topologies"
NETS_DIR = pathlib.Path(__file__).parent / "nets"

BASE_JSON = json.load(open(QUANTAS_TOPOLOGIES_DIR / "base.json", 'r'))

def read_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data

def get_json_files_in_directory(directory):
    json_files = []
    for file in pathlib.Path(directory).rglob('*.json'):
        json_files.append(file)
    return json_files

def extract_info(file_path):
    tmp = str(file_path).split("/nets/")[1]
    tmp = tmp.split("/")
    topology_type = tmp[0]
    topology_info = tmp[1]
    topology_name = tmp[2]
    return topology_type, topology_info, topology_name

def extract_connectivity_info(file_path):
    t_type, t_info, t_name = extract_info(file_path)
    connectivity = t_info.split("_")[2]
    return int(connectivity)

def extract_n_info(file_path):
    t_type, t_info, t_name = extract_info(file_path)
    n = t_info.split("_")[1]
    return int(n)
    
def select_random_byzantines(n, t):
    all_nodes = [i for i in range(1, n)]
    byzantines = random.sample(all_nodes, t)
    return byzantines

def graph_networkx_to_quantas(nx_graph):
    quantas_graph = {}
    for node in nx_graph["nodes"]:
        id = node["id"]
        neighbors = node["neighbors"]        
        quantas_graph[id] = neighbors
    
    return quantas_graph




    


    