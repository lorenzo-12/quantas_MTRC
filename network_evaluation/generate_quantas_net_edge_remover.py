from network_utils import *
from quantas_utils import *
import os


DIR_PATH = pathlib.Path(__file__).parent / "nets" / "edge_remover"
def clear_directory(dir_path = DIR_PATH):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
            
CSV_FILE = pathlib.Path(__file__).parent / "results" / "edge_remover.csv"
def clear_file_csv(csv_file = CSV_FILE):
    if os.path.exists(csv_file):
        os.remove(csv_file)
        

def load_settings(file: str = "settings/edge_remover.json"):
    with open(file, "r") as f:
        settings = json.load(f)
    
    n = settings.get("n", 100)
    min_k = settings.get("min_k", 3)
    max_k = settings.get("max_k", 10)
    attemps = settings.get("attempts", 1000)
    max_workers = settings.get("max_workers", 1)
    
    return n, min_k, max_k, attemps, max_workers



def generate_networks(n, k, attempts: int = 10000, net_to_generate: int = 10, combo: str = "dolev"):
    attempt = 1
    cnt = 0
    while attempt <= attempts and cnt < net_to_generate:
        
        G = nx.complete_graph(n)
            
        list_edges = list(G.edges())
        random.shuffle(list_edges)
        
        pca_network = networkx_to_network(G, PCANetwork)
        
        net, edge_removed_dolev = get_max_edge_removal(G.copy(), k, list_edges)
        dolev_network = networkx_to_network(net)
        
        edge_removed_pca = pca_network.get_max_edge_removal(k, list_edges)
        
        is_k_conncted = dolev_network.check_k_connectivity(k)
        is_k_level_ordering = pca_network.check_k_level_ordering(k)
        
        if combo=="dolev":
            print(f"removed edges from Dolev network! Saving...", flush=True)
            save_network(dolev_network, DIR_PATH / f"dolev_{n}_{k}", f"dolev_network{cnt}")
            cnt += 1
            
        if combo=="pca":
            print(f"removed edges from PCA network! Saving...", flush=True)
            save_network(pca_network, DIR_PATH / f"pca_{n}_{k}", f"pca_network{cnt}")
            cnt += 1

        if is_k_conncted and is_k_level_ordering and combo=="both":
            print(f"removed edges from both networks! Saving...", flush=True)
            save_network(dolev_network, DIR_PATH / f"both_{n}_{k}", f"both_network{cnt}")
            cnt += 1

        attempt += 1
            
    return cnt



""" k_val = 7
while True:
    print(RED + f"Trying to generate networks with k={k_val}" +  RESET, flush=True)
    x = generate_networks(n=50, k=k_val, attempts=1000, net_to_generate=10, combo="both")
    if x == 10:
        break 
    
    # delete folder and try again 
    clear_directory(DIR_PATH / f"both_{50}_{k_val}")
    os.rmdir(DIR_PATH / f"both_{50}_{k_val}")
    

k_val = 7
while True:
    print(BLUE + f"Trying to generate networks with k={k_val}" +  RESET, flush=True)
    x = generate_networks(n=50, k=k_val, attempts=1000, net_to_generate=10, combo="dolev")
    if x == 10:
        break 
    
    # delete folder and try again 
    clear_directory(DIR_PATH / f"both_{50}_{k_val}")
    os.rmdir(DIR_PATH / f"both_{50}_{k_val}") """
    
    

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


def get_output_file(n, k, t, topology_name="both_networks0"):
    return f"results/edge_remover_{n}_{k}_{t}_{topology_name}.json"


def create_experiment_json(nx_file, output_file, t, ts, tl):
    nx_graph = read_json(nx_file)
    quantas_graph = graph_networkx_to_quantas(nx_graph)
    base_exp = get_base_experiment_json()
    
    base_exp["logFile"] = output_file
    base_exp["threadCount"] = 48
    
    base_exp["parameters"]["t"] = t
    base_exp["parameters"]["ts"] = ts
    base_exp["parameters"]["tl"] = tl
    base_exp["parameters"]["byzantines"] = select_random_byzantines(100, t)
    
    base_exp["topology"]["list"] = quantas_graph
    base_exp["topology"]["initialPeers"] = 100
    
    base_exp["tests"] = 10
    base_exp["rounds"] = 1000
    
    return base_exp

x = get_json_files_in_directory(DIR_PATH)
k3 = []
k5 = []
k7 = []
for file in x:
    k = extract_connectivity_info(file)
    if k == 3:
        k3.append(file)
    elif k == 5:
        k5.append(file)
    elif k == 7:
        k7.append(file)
        

combinations = get_all_ts_tl_combinations(3)
final = {}
for t, ts, tl in combinations:
    if t not in final:
        final[t] = []
    for file in k3:
        n = extract_n_info(file)
        k = 3
        t_type, t_info, t_name = extract_info(file)
        output_file = get_output_file(n, k, t, file.stem)
        exp_json = create_experiment_json(file, output_file, t, ts, tl)
        final[t].append(exp_json)

    base = json.load(open("quantas_topologies/base.json", "r"))
    base["experiments"] = final[t]
    with open(f"quantas_topologies/experiments/edge_remover_n{n}_k{k}_t{t}.json", "w") as f:
        json.dump(base, f, indent=4)
    
        
combinations = get_all_ts_tl_combinations(5)
final = {}
for t, ts, tl in combinations:
    if t not in final:
        final[t] = []
    for file in k5:
        n = extract_n_info(file)
        k = 5
        t_type, t_info, t_name = extract_info(file)
        output_file = get_output_file(n, k, t, file.stem)
        exp_json = create_experiment_json(file, output_file, t, ts, tl)
        final[t].append(exp_json)

    base = json.load(open("quantas_topologies/base.json", "r"))
    base["experiments"] = final[t]
    with open(f"quantas_topologies/experiments/edge_remover_n{n}_k{k}_t{t}.json", "w") as f:
        json.dump(base, f, indent=4)
    
    
combinations = get_all_ts_tl_combinations(7)
final = {}
for t, ts, tl in combinations:
    if t not in final:
        final[t] = []
    for file in k7:
        n = extract_n_info(file)
        k = 7
        t_type, t_info, t_name = extract_info(file)
        output_file = get_output_file(n, k, t, file.stem)
        exp_json = create_experiment_json(file, output_file, t, ts, tl)
        final[t].append(exp_json)

    base = json.load(open("quantas_topologies/base.json", "r"))
    base["experiments"] = final[t]
    with open(f"quantas_topologies/experiments/edge_remover_n{n}_k{k}_t{t}.json", "w") as f:
        json.dump(base, f, indent=4)
        

dir = pathlib.Path(__file__).parent / "quantas_topologies" / "experiments"
k3 = ""
k5 = ""
k7 = ""
for file in dir.glob("edge_remover_n*_k*_t*.json"):
    js = json.load(open(file, "r"))
    exp = js["experiments"]
    if "k3" in file.stem:
        k3 += f"{file.stem}: {len(exp)} experiments\n"
    elif "k5" in file.stem:
        k5 += f"{file.stem}: {len(exp)} experiments\n"
    elif "k7" in file.stem:
        k7 += f"{file.stem}: {len(exp)} experiments\n"

print("k=3:")
print(k3)
print("k=5:")
print(k5)
print("k=7:")
print(k7)
