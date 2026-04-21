from network_utils import *
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
import sys
import csv
import argparse
import time

def clear_directory(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
            
def clear_file_csv(results_file):
    if os.path.exists(results_file):
        os.remove(results_file)
     

def append_result_to_file(results_file, d="_", k="_", edge_prob="_", pca_count="_", dolev_count="_", tries="_", edge_removed_pca_nets = "_", edge_removed_dolev_nets="_"):
    file_exists = os.path.exists(results_file)
    with open(results_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["d", "k", "edge_prob", "pca_count", "dolev_count", "attempts_per_edge_prob", "edge_removed_pca_nets", "edge_removed_dolev_nets"])
        writer.writerow([f"{d}", f"{k}", f"{edge_prob:.2f}", pca_count, dolev_count, tries, edge_removed_pca_nets, edge_removed_dolev_nets])

def load_settings(file: str = "settings/settings.json"):
    
    with open(file, "r") as f:
        settings = json.load(f)
    return settings

def get_remaining_tries(results_file, k, attempts_per_edge_prob, min_edge_prob: float = 0.0, max_edge_prob: float = 1.0, d: str="_"):
    remaining_tries = [round(i/100, 2) for i in range(int(min_edge_prob * 100), int(max_edge_prob * 100) + 1)]
    
    if not os.path.exists(results_file):
        return remaining_tries
    
    lines = open(results_file, "r").readlines()
    for line in lines[1:]:  # Skip header
        if line.strip() == "":
            continue
        d_val, k_val, edge_prob, pca_count, dolev_count, attempt, edge_removed_pca_nets, edge_removed_dolev_nets = line.strip().split(",")
        if k == int(k_val) and d_val == "_":
            edge_prob = round(float(edge_prob), 2)
            attempt = int(attempt)
            if attempt == attempts_per_edge_prob and edge_prob in remaining_tries:
                remaining_tries.remove(edge_prob)
        
        elif k == int(k_val) and d_val != "_" and d == int(d_val): 
            edge_prob = round(float(edge_prob), 2)
            attempt = int(attempt)
            if attempt == attempts_per_edge_prob and edge_prob in remaining_tries:
                remaining_tries.remove(edge_prob)
    
    return remaining_tries
            


def generate_networks(network_type, n, k, edge_prob, attempts: int = 10000, nets_dir: pathlib.Path = pathlib.Path("nets"), progress_counter=None, progress_lock=None, total_attempts=None, stop_flag=None):
    attempt = 1
    pca_nets = []
    dolev_nets = []
    edge_removed_dolev_nets = []
    edge_removed_pca_nets = []
    clear_directory(nets_dir / f"pca_{n}_{k}_{edge_prob:.2f}")
    clear_directory(nets_dir / f"dolev_{n}_{k}_{edge_prob:.2f}")
    while attempt <= attempts:
        #print(f"attempt {attempt}", flush=True)
        if stop_flag is not None and stop_flag.value:
            break
        #print(f"-------- Attempt {attempt:4} - n:{n:3} - p:{edge_prob:.2f} - k:{k:2} --------")
        if network_type == "erdos_renyi":
            G = nx.erdos_renyi_graph(n, edge_prob)
        elif network_type == "watts_strogatz":
            G = nx.watts_strogatz_graph(n, k, edge_prob)
        elif network_type == "random_regular":
            G = nx.random_regular_graph(k, n)
        elif network_type == "edge_remover":
            G = nx.complete_graph(n)
        else:
            raise ValueError(f"Unsupported network type: {network_type}")
        
        
        if network_type == "edge_remover":
            list_edges = list(G.edges())
            random.shuffle(list_edges)
            
            pca_network = networkx_to_network(G, PCANetwork)
            
            start = time.time()
            net, edge_removed_dolev = get_max_edge_removal(G.copy(), k, list_edges)
            edge_removed_dolev_nets.append((edge_removed_dolev, attempt))
            dolev_nets.append((networkx_to_network(net), attempt))
            end = time.time()
            #print(f"attempt {attempt} Time taken for Dolev's algorithm: {end - start:.2f} seconds", flush=True)
            
            start = time.time()
            edge_removed_pca = pca_network.get_max_edge_removal(k, list_edges)
            edge_removed_pca_nets.append((edge_removed_pca, attempt))
            pca_nets.append((pca_network, attempt))
            end = time.time()
            #print(f"attempt {attempt} Time taken for PCA algorithm: {end - start:.2f} seconds", flush=True)
            
            
        else:
            network = networkx_to_network(G)
            pca_network = networkx_to_network(G, PCANetwork)
            
            is_k_conncted = network.check_k_connectivity(k)
            is_k_level_ordering = pca_network.check_k_level_ordering(k)
            
            
            if is_k_conncted:
                #print(f"{GREEN}Generated graph is at least {k}-connected{RESET}")
                dolev_nets.append((network, attempt))
                
            if is_k_level_ordering:
                #print(f"{GREEN}Generated graph is a {k}-level-ordering{RESET}")
                pca_nets.append((pca_network, attempt))
                
                
        #print(f"-----------------------------------")
        if progress_counter is not None and progress_lock is not None and total_attempts is not None:
            with progress_lock:
                progress_counter.value += 1
                completed = progress_counter.value
                progress = min(completed / total_attempts, 1.0)
                
                if completed % 250 == 0 or completed >= total_attempts:
                    #os.system("clear")
                    bar_len = 100
                    filled = int(bar_len * progress)
                    bar = "#" * filled + "_" * (bar_len - filled)
                    percent = int(100 * progress)
                    sys.stdout.write(f"Checking n:{n:3} - k:{k:2}\n")
                    sys.stdout.write(f"\rstatus: {bar} : {percent}%\n")
                    sys.stdout.flush()
                    if completed >= total_attempts:
                        print()

        attempt += 1

    for net, attempt in pca_nets:
        save_network(net, nets_dir / f"pca_{n}_{k}_{edge_prob:.2f}", f"pca_network{attempt}")

    for net, attempt in dolev_nets:
        save_network(net, nets_dir / f"dolev_{n}_{k}_{edge_prob:.2f}", f"dolev_network{attempt}")
        
    avg_edge_removed_pca_nets = sum([x[0] for x in edge_removed_pca_nets]) / len(edge_removed_pca_nets) if edge_removed_pca_nets else 0
    avg_edge_removed_dolev_nets = sum([x[0] for x in edge_removed_dolev_nets]) / len(edge_removed_dolev_nets) if edge_removed_dolev_nets else 0
    
    return edge_prob, len(pca_nets), len(dolev_nets), avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets



def erdos_renyi_experiment(settings):
    json_settings = load_settings(settings)
    
    network_type = json_settings.get("network", "erdos_renyi")
    results_file = json_settings.get("results_file", "results/erdos_renyi.csv")
    n = json_settings.get("n", 100)
    min_k = json_settings.get("min_k", 1)
    max_k = json_settings.get("max_k", 10)
    min_edge_prob = json_settings.get("min_edge_prob", 0.01)
    max_edge_prob = json_settings.get("max_edge_prob", 1.00)
    attempts_per_edge_prob = json_settings.get("attempts_per_edge_prob", 1000)
    max_workers = json_settings.get("thread_pool_size", 1)
    nets_dir = json_settings.get("nets_dir", pathlib.Path("nets") / "erdos_renyi")
    
    for k in range(min_k, max_k + 1):
        
        edges_prob = get_remaining_tries(results_file=results_file, k=k, attempts_per_edge_prob=attempts_per_edge_prob, min_edge_prob=min_edge_prob, max_edge_prob=max_edge_prob)
        print(f"Remaining edge probabilities for k={k}: {edges_prob}", flush=True)
        if edges_prob == []:
            print(f"All edge probabilities have been processed for k={k}. No remaining tries.", flush=True)
            continue

        manager = Manager()
        progress_counter = manager.Value('i', 0)
        progress_lock = manager.Lock()
        stop_flag = manager.Value('b', False)
        
        list_results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            total_attempts = len(edges_prob) * attempts_per_edge_prob
            future_to_prob = {}
            for edge_prob in edges_prob:
                future = executor.submit(generate_networks, network_type, n, k, edge_prob, attempts=attempts_per_edge_prob, nets_dir=nets_dir, progress_counter=progress_counter, progress_lock=progress_lock, total_attempts=total_attempts, stop_flag=stop_flag)
                future_to_prob[future] = edge_prob

            try:
                for future in as_completed(future_to_prob):
                    edge_prob = future_to_prob[future]
                    try:
                        edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets = future.result()
                        print("saving results to file...", flush=True)
                        append_result_to_file(results_file=results_file, d="_", k=k, edge_prob=edge_prob, pca_count=pca_count, dolev_count=dolev_count, tries=attempts_per_edge_prob, edge_removed_pca_nets="_", edge_removed_dolev_nets="_")
                        list_results.extend([(edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets)])
                    except Exception as exc:
                        print(f"[main] Edge probability {edge_prob:.2f} generated an exception: {exc}", flush=True)
            except KeyboardInterrupt:
                stop_flag.value = True
                print("\nCtrl+C received, shutting down threads...", flush=True)
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        #list_results.sort(key=lambda x: x[0])
        #print_results(list_results, n, k, attempts_per_edge_prob)
        
        

def random_regular_experiment(settings):
    json_settings = load_settings(settings)
    
    network_type = json_settings.get("network", "random_regular")
    results_file = json_settings.get("results_file", "results/random_regular.csv")
    n = json_settings.get("n", 100)
    min_k = json_settings.get("min_k", 1)
    max_k = json_settings.get("max_k", 10)
    min_d = json_settings.get("min_d", 10)
    max_d = json_settings.get("max_d", 50)
    attempts_per_edge_prob = json_settings.get("attempts_per_edge_prob", 1000)
    max_workers = json_settings.get("thread_pool_size", 1)
    nets_dir = json_settings.get("nets_dir", pathlib.Path("nets") / "random_regular")

    print(f"Starting Random Regular experiment with d in [{min_d}, {max_d}]", flush=True)
    for d in range(min_d, max_d + 1, 2):
        max_k = min(max_k, d)
        print(f"Processing d={d} with max_k={max_k}", flush=True)
        for k in range(min_k, max_k + 1):
            
            edges_prob = get_remaining_tries(results_file=results_file, k=k, attempts_per_edge_prob=attempts_per_edge_prob, min_edge_prob="_", max_edge_prob="_")
            print(f"Remaining edge probabilities for k={k}: {edges_prob}", flush=True)
            if edges_prob == []:
                print(f"All edge probabilities have been processed for k={k}. No remaining tries.", flush=True)
                continue

            manager = Manager()
            progress_counter = manager.Value('i', 0)
            progress_lock = manager.Lock()
            stop_flag = manager.Value('b', False)
            
            list_results = []
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                total_attempts = len(edges_prob) * attempts_per_edge_prob
                future_to_prob = {}
                for edge_prob in edges_prob:
                    future = executor.submit(generate_networks, network_type, n, k, edge_prob, attempts=attempts_per_edge_prob, nets_dir=nets_dir, progress_counter=progress_counter, progress_lock=progress_lock, total_attempts=total_attempts, stop_flag=stop_flag)
                    future_to_prob[future] = edge_prob

                try:
                    for future in as_completed(future_to_prob):
                        edge_prob = future_to_prob[future]
                        try:
                            edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets = future.result()
                            print("saving results to file...", flush=True)
                            append_result_to_file(results_file=results_file, d="_", k=k, edge_prob=edge_prob, pca_count=pca_count, dolev_count=dolev_count, tries=attempts_per_edge_prob, edge_removed_pca_nets="_", edge_removed_dolev_nets="_")
                            list_results.extend([(edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets)])
                        except Exception as exc:
                            print(f"[main] Edge probability {edge_prob:.2f} generated an exception: {exc}", flush=True)
                except KeyboardInterrupt:
                    stop_flag.value = True
                    print("\nCtrl+C received, shutting down threads...", flush=True)
                    executor.shutdown(wait=False, cancel_futures=True)
                    raise

            #list_results.sort(key=lambda x: x[0])
            #print_results(list_results, n, k, attempts_per_edge_prob)
        

def edge_remover_experiments(settings):
    json_settings = load_settings(settings)
    
    network_type = json_settings.get("network", "edge_remover")
    results_file = json_settings.get("results_file", "results/edge_remover.csv")
    n = json_settings.get("n", 100)
    min_k = json_settings.get("min_k", 1)
    max_k = json_settings.get("max_k", 10)
    attempts_per_edge_prob = json_settings.get("attempts_per_edge_prob", 1000)
    max_workers = json_settings.get("thread_pool_size", 1)
    nets_dir = json_settings.get("nets_dir", pathlib.Path("nets") / "edge_remover")
    
    for k in range(min_k, max_k + 1):
        
        edges_prob = get_remaining_tries(results_file=results_file, k=k, attempts_per_edge_prob=attempts_per_edge_prob, min_edge_prob="_", max_edge_prob="_")
        print(f"Remaining edge probabilities for k={k}: {edges_prob}", flush=True)
        if edges_prob == []:
            print(f"All edge probabilities have been processed for k={k}. No remaining tries.", flush=True)
            continue

        manager = Manager()
        progress_counter = manager.Value('i', 0)
        progress_lock = manager.Lock()
        stop_flag = manager.Value('b', False)
        
        list_results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            total_attempts = len(edges_prob) * attempts_per_edge_prob
            future_to_prob = {}
            for edge_prob in edges_prob:
                future = executor.submit(generate_networks, network_type, n, k, edge_prob, attempts=attempts_per_edge_prob, nets_dir=nets_dir, progress_counter=progress_counter, progress_lock=progress_lock, total_attempts=total_attempts, stop_flag=stop_flag)
                future_to_prob[future] = edge_prob

            try:
                for future in as_completed(future_to_prob):
                    edge_prob = future_to_prob[future]
                    try:
                        edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets = future.result()
                        print("saving results to file...", flush=True)
                        append_result_to_file(results_file=results_file, d="_", k=k, edge_prob=edge_prob, pca_count=pca_count, dolev_count=dolev_count, tries=attempts_per_edge_prob, edge_removed_pca_nets=edge_removed_pca_nets, edge_removed_dolev_nets=edge_removed_dolev_nets)
                        list_results.extend([(edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets)])
                    except Exception as exc:
                        print(f"[main] Edge probability {edge_prob:.2f} generated an exception: {exc}", flush=True)
            except KeyboardInterrupt:
                stop_flag.value = True
                print("\nCtrl+C received, shutting down threads...", flush=True)
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        #list_results.sort(key=lambda x: x[0])
        #print_results(list_results, n, k, attempts_per_edge_prob)
        
        
def watts_strogatz_experiment(settings):
    network_type, n, min_d, max_d, min_k, max_k, min_edge_prob, max_edge_prob, attempts_per_edge_prob, max_workers, results_file, nets_dir = load_settings(settings)
    

    for k in range(min_k, max_k + 1):
        
        edges_prob = get_remaining_tries(results_file=results_file, k=k, attempts_per_edge_prob=attempts_per_edge_prob, min_edge_prob=min_edge_prob, max_edge_prob=max_edge_prob)
        print(f"Remaining edge probabilities for k={k}: {edges_prob}", flush=True)
        if edges_prob == []:
            print(f"All edge probabilities have been processed for k={k}. No remaining tries.", flush=True)
            continue

        manager = Manager()
        progress_counter = manager.Value('i', 0)
        progress_lock = manager.Lock()
        stop_flag = manager.Value('b', False)
        
        list_results = []
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            total_attempts = len(edges_prob) * attempts_per_edge_prob
            future_to_prob = {}
            for edge_prob in edges_prob:
                future = executor.submit(generate_networks, network_type, n, k, edge_prob, attempts=attempts_per_edge_prob, nets_dir=nets_dir, progress_counter=progress_counter, progress_lock=progress_lock, total_attempts=total_attempts, stop_flag=stop_flag)
                future_to_prob[future] = edge_prob

            try:
                for future in as_completed(future_to_prob):
                    edge_prob = future_to_prob[future]
                    try:
                        edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets = future.result()
                        print("saving results to file...", flush=True)
                        append_result_to_file(results_file=results_file, d="_", k=k, edge_prob=edge_prob, pca_count=pca_count, dolev_count=dolev_count, tries=attempts_per_edge_prob, edge_removed_pca_nets="_", edge_removed_dolev_nets="_")
                        list_results.extend([(edge_prob, pca_count, dolev_count, edge_removed_pca_nets, edge_removed_dolev_nets)])
                    except Exception as exc:
                        print(f"[main] Edge probability {edge_prob:.2f} generated an exception: {exc}", flush=True)
            except KeyboardInterrupt:
                stop_flag.value = True
                print("\nCtrl+C received, shutting down threads...", flush=True)
                executor.shutdown(wait=False, cancel_futures=True)
                raise

        #list_results.sort(key=lambda x: x[0])
        #print_results(list_results, n, k, attempts_per_edge_prob)
        
        
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--net", default="settings/settings.json")
    args = parser.parse_args()

    if args.net == "settings/erdos_renyi.json":
        erdos_renyi_experiment(args.net)
    elif args.net == "settings/watts_strogatz.json":
        watts_strogatz_experiment(args.net)
    elif args.net == "settings/random_regular.json":
        random_regular_experiment(args.net)
    elif args.net == "settings/edge_remover.json":
        edge_remover_experiments(args.net)
    else:
        print(f"Unsupported network type: {args.net}")