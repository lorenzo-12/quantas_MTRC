from network_utils import *
from quantas_utils import *
import os

QUANTAS_TOPOLOGIES_PATH = pathlib.Path(__file__).parent.parent / "Quantas" / "quantas" / "topologies"

DIR_PATH = pathlib.Path(__file__).parent / "nets" / "erdos_renyi"
def clear_directory(dir_path = DIR_PATH):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
            
CSV_FILE = pathlib.Path(__file__).parent / "results" / "erdos_renyi.csv"
def clear_file_csv(csv_file = CSV_FILE):
    if os.path.exists(csv_file):
        os.remove(csv_file)
        

def load_settings(file: str = "settings/erdos_renyi.json"):
    with open(file, "r") as f:
        settings = json.load(f)
    
    n = settings.get("n", 100)
    min_k = settings.get("min_k", 3)
    max_k = settings.get("max_k", 10)
    attemps = settings.get("attempts", 1000)
    min_edge_prob = settings.get("min_edge_prob", 0.01)
    max_edge_prob = settings.get("max_edge_prob", 1.00)
    max_workers = settings.get("max_workers", 1)
    
    return n, min_k, max_k, attemps, min_edge_prob, max_edge_prob, max_workers


def generate_networks(n, k, edge_prob, attempts: int = 1000, net_to_generate: int = 10, combo: str = "dolev"):
    attempt = 1
    cnt = 0
    while attempt <= attempts and cnt < net_to_generate:
        #print(f"attempt {attempt}", flush=True)
        
        G = nx.erdos_renyi_graph(n, edge_prob)
            
        dolev_network = networkx_to_network(G)
        pca_network = networkx_to_network(G, PCANetwork)
        
        is_k_conncted = dolev_network.check_k_connectivity(k)
        is_k_level_ordering = pca_network.check_k_level_ordering(k)
        
        
        if is_k_conncted and combo=="dolev":
            print(f"Found a {k}-connected network! Saving...", flush=True)
            save_network(dolev_network, DIR_PATH / f"dolev_{n}_{k}_{edge_prob:.2f}", f"dolev_network{cnt}")
            cnt += 1
            
        if is_k_level_ordering and combo=="pca":
            print(f"Found a network with a {k}-level ordering! Saving...", flush=True)
            save_network(pca_network, DIR_PATH / f"pca_{n}_{k}_{edge_prob:.2f}", f"pca_network{cnt}")
            cnt += 1

        if is_k_conncted and is_k_level_ordering and combo=="both":
            print(f"Found a network that is both {k}-connected and has a {k}-level ordering! Saving...", flush=True)
            save_network(dolev_network, DIR_PATH / f"both_{n}_{k}_{edge_prob:.2f}", f"both_network{cnt}")
            cnt += 1
            
        attempt += 1
    
    return cnt


""" for n_val in [50, 100]:
    edge_prob_val_both = 0.10
    edge_prob_val_dolev = 0.10
    for k_val in [3, 5, 7]:
        while True:
            print(RED + f"Trying to generate networks with k={k_val} and edge probability={edge_prob_val_both:.2f}" +  RESET, flush=True)
            x = generate_networks(n=n_val, k=k_val, edge_prob=edge_prob_val_both, attempts=1000, net_to_generate=10, combo="both")
            if x == 10:
                break 
            
            # delete folder and try again 
            clear_directory(DIR_PATH / f"both_{n_val}_{k_val}_{edge_prob_val_both:.2f}")
            os.rmdir(DIR_PATH / f"both_{n_val}_{k_val}_{edge_prob_val_both:.2f}")
            edge_prob_val_both += 0.01

        while True:
            print(BLUE + f"Trying to generate networks with k={k_val} and edge probability={edge_prob_val_dolev:.2f}" +  RESET, flush=True)
            x = generate_networks(n=n_val, k=k_val, edge_prob=edge_prob_val_dolev, attempts=1000, net_to_generate=10, combo="dolev")
            if x == 10:
                break 
            
            # delete folder and try again 
            clear_directory(DIR_PATH / f"dolev_{n_val}_{k_val}_{edge_prob_val_dolev:.2f}")
            os.rmdir(DIR_PATH / f"dolev_{n_val}_{k_val}_{edge_prob_val_dolev:.2f}")
            edge_prob_val_dolev += 0.01 """
    
    

def get_all_ts_tl_combinations(k):
    k = k-1
    combinations = []
    for ts in range(1,k):
        combinations.append((ts, k - ts))
        
    ret = []
    k = k+1
    for ts,tl in combinations:
        for t in range(1, 2*k):
            ret.append((t, ts, tl))
            
    return ret

def get_base_experiment_json():
    exp = json.load(open("quantas_topologies/base.json", "r"))
    return exp["experiments"][0]


def get_output_file(n, k, t, topology_name="both_networks0", algorithm="dolev"):
    return f"results/{algorithm}_erdos_renyi_{n}_{k}_{t}_{topology_name}.json"


def create_experiment_json(nx_file, output_file, t, ts, tl, n, algorithm):
    nx_graph = read_json(nx_file)
    quantas_graph = graph_networkx_to_quantas(nx_graph)
    base_exp = get_base_experiment_json()
    
    base_exp["logFile"] = output_file
    base_exp["threadCount"] = 48
    
    base_exp["parameters"]["t"] = t
    base_exp["parameters"]["ts"] = ts
    base_exp["parameters"]["tl"] = tl
    base_exp["parameters"]["byzantines"] = select_random_byzantines(n, t)
    
    base_exp["topology"]["list"] = quantas_graph
    base_exp["topology"]["initialPeers"] = n
    base_exp["topology"]["initialPeerType"] = "CPAPeer" if algorithm == "cpa" else "DolevPeer"
    
    base_exp["tests"] = 10
    base_exp["rounds"] = 1000
    
    return base_exp


def get_json_files(n,k):
    x = get_json_files_in_directory(DIR_PATH)
    ret = []
    for file in x:
        a,b = extract_n_k_info(file)
        if a == n and b == k:
            ret.append(file)
    return ret


for n in [50, 100]:
    for algorithm in ["dolev", "pca"]:
        for k in [3, 5, 7]:
            combinations = get_all_ts_tl_combinations(k)
            final = {}
            for t, ts, tl in combinations:
                if t not in final:
                    final[t] = []
                for file in get_json_files(n, k):
                    t_type, t_info, t_name = extract_info(file)
                    output_file = get_output_file(n, k, t, file.stem, algorithm)
                    exp_json = create_experiment_json(file, output_file, t, ts, tl, n, algorithm)
                    final[t].append(exp_json)
                
                base = json.load(open("quantas_topologies/base.json", "r"))
                if algorithm == "dolev":
                    base["algorithms"] = ["DolevPeer/DolevPeer.cpp"]
                elif algorithm == "cpa":
                    base["algorithms"] = ["CPAPeer/CPAPeer.cpp"]

                base["experiments"] = final[t]
                with open(f"{str(QUANTAS_TOPOLOGIES_PATH)}/{algorithm}_erdos_renyi_n{n}_k{k}_t{t}.json", "w") as f:
                    json.dump(base, f, indent=4)
        

