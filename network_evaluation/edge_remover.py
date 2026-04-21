from network_utils import *
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
import sys
import csv

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


def append_result_to_file(n, k, pca_count, dolev_count, avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets, attempts):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["n", "k", "pca_count", "dolev_count", "avg_edge_removed_pca_nets", "avg_edge_removed_dolev_nets", "attempts"])
        writer.writerow([f"{n}", f"{k}", pca_count, dolev_count, avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets, attempts])
        

def get_remaining_tries(min_k: int, max_k:int, attempts: int):
    remaining_tries = [k for k in range(min_k, max_k+1)]
    
    if not os.path.exists(CSV_FILE):
        return remaining_tries
    
    lines = open(CSV_FILE, "r").readlines()
    for line in lines[1:]:  # Skip header
        if line.strip() == "":
            continue
        _, k_val, _, _, _, _, attempt = line.strip().split(",")
        k_val = int(k_val)
        if attempt == attempts and k_val in remaining_tries:
            remaining_tries.remove(k_val)
    
    return remaining_tries


def generate_networks(n, k, attempts: int = 10000, progress_counter=None, progress_lock=None, total_attempts=None, stop_flag=None):
    attempt = 1
    pca_nets = []
    dolev_nets = []
    edge_removed_dolev_nets = []
    edge_removed_pca_nets = []
    while attempt <= attempts:
        #print(f"attempt {attempt}", flush=True)
        if stop_flag is not None and stop_flag.value:
            break
        
        G = nx.complete_graph(n)
            
        list_edges = list(G.edges())
        random.shuffle(list_edges)
        
        pca_network = networkx_to_network(G, PCANetwork)
        
        net, edge_removed_dolev = get_max_edge_removal(G.copy(), k, list_edges)
        edge_removed_dolev_nets.append((edge_removed_dolev, attempt))
        dolev_nets.append((networkx_to_network(net), attempt))
        
        edge_removed_pca = pca_network.get_max_edge_removal(k, list_edges)
        edge_removed_pca_nets.append((edge_removed_pca, attempt))
        pca_nets.append((pca_network, attempt))
                
                
        #print(f"-----------------------------------")
        if progress_counter is not None and progress_lock is not None and total_attempts is not None:
            with progress_lock:
                progress_counter.value += 1
                completed = progress_counter.value
                progress = min(completed / total_attempts, 1.0)
                
                if completed % 20 == 0 or completed >= total_attempts:
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

    """ for net, attempt in pca_nets:
        save_network(net, DIR_PATH / f"pca_{n}_{k}", f"pca_network{attempt}")

    for net, attempt in dolev_nets:
        save_network(net, DIR_PATH / f"dolev_{n}_{k}", f"dolev_network{attempt}") """
    
    avg_edge_removed_pca_nets = sum([x[0] for x in edge_removed_pca_nets]) / len(edge_removed_pca_nets) if edge_removed_pca_nets else 0
    avg_edge_removed_dolev_nets = sum([x[0] for x in edge_removed_dolev_nets]) / len(edge_removed_dolev_nets) if edge_removed_dolev_nets else 0
    
    
    return k, len(pca_nets), len(dolev_nets), avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets


def edge_remover_plot():
    results = "results/edge_remover.csv"
    if not os.path.exists(results):
        print(f"No results file found at {results}. Please run the edge_remover script first.")
        return

    res = {}
    with open(results, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 7:
                continue
            n, k, pca_count, dolev_count, avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets, attempts = row
            n = int(n)
            k = int(k)
            pca_count = int(pca_count)
            dolev_count = int(dolev_count)
            avg_edge_removed_pca_nets = float(avg_edge_removed_pca_nets)
            avg_edge_removed_dolev_nets = float(avg_edge_removed_dolev_nets)
            attempts = int(attempts)

            if n != 100:
                continue
            if k not in res:
                res[k] = [avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets]
    
    ks = sorted(res.keys())
    avg_edge_removed_pca_nets = [res[k][0] for k in ks]
    avg_edge_removed_dolev_nets = [res[k][1] for k in ks]
    plt.figure(figsize=(10, 7))
    plt.plot(ks, avg_edge_removed_pca_nets, marker='o', label='PCA Networks')
    plt.plot(ks, avg_edge_removed_dolev_nets, marker='o', label='Dolev Networks')
    plt.xlabel('connectivity (k)', fontsize=FT)
    plt.xticks(ks, fontsize=FT-4)
    plt.ylabel('Average Edges Removed \nto Disconnect Network', fontsize=FT)
    plt.ylim(top=5000)
    plt.yticks(fontsize=FT-4)
    plt.title('Edge Removal Comparison for a network of n=100 nodes\n on 1000 attempts', fontsize=FT)
    plt.legend(fontsize=FT-3)
    plt.savefig("img/edge_remover_plot.png", dpi=600)
    plt.savefig("img/edge_remover_plot.pdf", dpi=600)
    
    
    results = "results/edge_remover.csv"
    if not os.path.exists(results):
        print(f"No results file found at {results}. Please run the edge_remover script first.")
        return

    res = {}
    with open(results, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 7:
                continue
            n, k, pca_count, dolev_count, avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets, attempts = row
            n = int(n)
            k = int(k)
            pca_count = int(pca_count)
            dolev_count = int(dolev_count)
            avg_edge_removed_pca_nets = float(avg_edge_removed_pca_nets)
            avg_edge_removed_dolev_nets = float(avg_edge_removed_dolev_nets)
            attempts = int(attempts)

            if n != 100:
                continue
            if k not in res:
                res[k] = [5000 - avg_edge_removed_pca_nets, 5000 -avg_edge_removed_dolev_nets]
    
    ks = sorted(res.keys())
    avg_edge_removed_pca_nets = [res[k][0] for k in ks]
    avg_edge_removed_dolev_nets = [res[k][1] for k in ks]
    plt.figure(figsize=(10, 7))
    plt.plot(ks, avg_edge_removed_pca_nets, marker='o', label='PCA Networks')
    plt.plot(ks, avg_edge_removed_dolev_nets, marker='o', label='Dolev Networks')
    plt.xlabel('connectivity (k)', fontsize=FT)
    plt.xticks(ks, fontsize=FT-4)
    plt.ylabel('Average Minimum Edges needed\n to keep Network Connected', fontsize=FT)
    plt.ylim(top=5000)
    plt.yticks(fontsize=FT-4)
    plt.title('Edge Removal Inverse Comparison for a network of n=100 nodes\n on 1000 attempts', fontsize=FT)
    plt.legend(fontsize=FT-3)
    plt.savefig("img/edge_remover_plot_inverse.png", dpi=600)
    plt.savefig("img/edge_remover_plot_inverse.pdf", dpi=600)



if __name__ == "__main__":
    edge_remover_plot()
    """ n, min_k, max_k, attempts, max_workers = load_settings()
    remaining_k = get_remaining_tries(min_k, max_k, attempts)
    print(f"[edge_remover] Remaining k values: {remaining_k}", flush=True)
    if remaining_k == []:
        print(f"[edge_remover] All k values have been processed. No remaining tries.", flush=True)
        exit()
    
    for k in remaining_k:

        clear_directory(DIR_PATH / f"pca_{n}_{k}")
        clear_directory(DIR_PATH / f"dolev_{n}_{k}")
        manager = Manager()
        progress_counter = manager.Value('i', 0)
        progress_lock = manager.Lock()
        stop_flag = manager.Value('b', False)
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            total_attempts = attempts
            future = executor.submit(
                generate_networks,
                n,
                k,
                attempts=attempts,
                progress_counter=progress_counter,
                progress_lock=progress_lock,
                total_attempts=total_attempts,
                stop_flag=stop_flag
            )

            try:
                k, pca_count, dolev_count, avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets = future.result()
                append_result_to_file(
                    n, k, pca_count, dolev_count,
                    avg_edge_removed_pca_nets, avg_edge_removed_dolev_nets, attempts
                )
            except Exception as exc:
                print(f"[main] generated an exception: {exc}", flush=True) """
