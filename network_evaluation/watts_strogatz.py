from network_utils import *
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import Manager
import sys
import csv
import matplotlib.colors as mcolors

DIR_PATH = pathlib.Path(__file__).parent / "nets" / "watts_strogatz"
def clear_directory(dir_path = DIR_PATH):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    for filename in os.listdir(dir_path):
        file_path = os.path.join(dir_path, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
            
CSV_FILE = pathlib.Path(__file__).parent / "results" / "watts_strogatz.csv"
def clear_file_csv(csv_file = CSV_FILE):
    if os.path.exists(csv_file):
        os.remove(csv_file)
        

def load_settings(file: str = "settings/watts_strogatz.json"):
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


def append_result_to_file(n, k, edge_prob, pca_count, dolev_count, attempts):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["n", "k", "edge_prob", "pca_count", "dolev_count", "attempts"])
        writer.writerow([f"{n}", f"{k}", f"{edge_prob:.2f}", pca_count, dolev_count, attempts])
        

def get_remaining_tries(k: int, attempts: int, min_edge_prob: float, max_edge_prob: float):
    remaining_tries = [round(i/100, 2) for i in range(int(min_edge_prob * 100), int(max_edge_prob * 100) + 1)]
    
    if not os.path.exists(CSV_FILE):
        return remaining_tries
    
    lines = open(CSV_FILE, "r").readlines()
    for line in lines[1:]:  # Skip header
        if line.strip() == "":
            continue
        n_val, k_val, edge_prob, pca_count, dolev_count, attempt = line.strip().split(",")
        if k == int(k_val):
            edge_prob = round(float(edge_prob), 2)
            attempt = int(attempt)
            if attempt == attempts and edge_prob in remaining_tries:
                remaining_tries.remove(edge_prob)
    
    return remaining_tries


def generate_networks(n, k, edge_prob, attempts: int = 10000, progress_counter=None, progress_lock=None, total_attempts=None, stop_flag=None):
    attempt = 1
    pca_nets = []
    dolev_nets = []
    while attempt <= attempts:
        #print(f"attempt {attempt}", flush=True)
        if stop_flag is not None and stop_flag.value:
            break
        
        G = nx.watts_strogatz_graph(n, k, edge_prob)
            
        dolev_network = networkx_to_network(G)
        pca_network = networkx_to_network(G, PCANetwork)
        
        is_k_conncted = dolev_network.check_k_connectivity(k)
        is_k_level_ordering = pca_network.check_k_level_ordering(k)
        
        
        if is_k_conncted:
            #print(f"{GREEN}Generated graph is at least {k}-connected{RESET}")
            dolev_nets.append((dolev_network, attempt))
            
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

    """ for net, attempt in pca_nets:
        save_network(net, DIR_PATH / f"pca_{n}_{k}_{edge_prob:.2f}", f"pca_network{attempt}")

    for net, attempt in dolev_nets:
        save_network(net, DIR_PATH / f"dolev_{n}_{k}_{edge_prob:.2f}", f"dolev_network{attempt}") """
    
    return edge_prob, len(pca_nets), len(dolev_nets)


def watts_strogatz_plot():
    results = "results/watts_strogatz.csv"
    if not os.path.exists(results):
        print(f"No results file found at {results}. Please run the watts_strogatz script first.")
        return

    res = {}
    with open(results, "r") as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 6:
                continue
            n, k, edge_prob, pca_count, dolev_count, attempts = row
            n = int(n)
            k = int(k)
            edge_prob = float(edge_prob)
            pca_count = int(pca_count)
            dolev_count = int(dolev_count)
            attempts = int(attempts)

            if n != 100:
                continue
            if k not in res:
                res[k] = {}
            if edge_prob not in res[k] and edge_prob <= 0.50:
                res[k][edge_prob] = (pca_count, dolev_count)
    
    ks = sorted(res.keys())
    edge_probs = sorted(res[ks[0]].keys()) if ks else []
    
    plt.figure(figsize=(10, 6))
    

    num_colors = int(len(ks))
    color_list = list(mcolors.TABLEAU_COLORS.values())

    def adjust_color(color, factor):
        r, g, b = mcolors.to_rgb(color)
        if factor > 1:
            r = r + (1 - r) * (factor - 1)
            g = g + (1 - g) * (factor - 1)
            b = b + (1 - b) * (factor - 1)
        else:
            r *= factor
            g *= factor
            b *= factor
        return (min(max(r, 0), 1), min(max(g, 0), 1), min(max(b, 0), 1))

    base_colors = [color_list[i % len(color_list)] for i in range(num_colors)]
    pca_colors = [adjust_color(color, 1.3) for color in base_colors]
    dolev_colors = [adjust_color(color, 0.7) for color in base_colors]

    for i, k in enumerate(ks):
        pca_counts = [res[k][edge_prob][0] for edge_prob in edge_probs]
        pca_percentage = [count / 1000 * 100 for count in pca_counts]
        dolev_counts = [res[k][edge_prob][1] for edge_prob in edge_probs]
        dolev_percentage = [count / 1000 * 100 for count in dolev_counts]
        
        pca_ci = [wilson_ci(pca_count, attempts) for pca_count in pca_counts]
        dolev_ci = [wilson_ci(dolev_count, attempts) for dolev_count in dolev_counts]
        pca_ci_lower = [ci[0] * 100 for ci in pca_ci]
        pca_ci_upper = [ci[1] * 100 for ci in pca_ci]
        dolev_ci_lower = [ci[0] * 100 for ci in dolev_ci]
        dolev_ci_upper = [ci[1] * 100 for ci in dolev_ci]

        plt.plot(edge_probs, pca_percentage, label=f'PCA k={k}', color=pca_colors[i], linestyle='-')
        plt.fill_between(edge_probs, pca_ci_lower, pca_ci_upper, color=pca_colors[i], alpha=0.15)
        plt.plot(edge_probs, dolev_percentage, label=f'Dolev k={k}', color=dolev_colors[i], linestyle='--')
        plt.fill_between(edge_probs, dolev_ci_lower, dolev_ci_upper, color=dolev_colors[i], alpha=0.15)
    
    
    plt.xlabel('rewiring probability (p)', fontsize=FT)
    plt.xticks([round(i/100, 2) for i in range(0, 51, 10)], fontsize=FT-4)
    plt.ylabel('percentage of networks that are\n connected out of 1000 attempts', fontsize=FT)
    plt.ylim(top=110)
    plt.yticks([0, 20, 40, 60, 80, 100], fontsize=FT-4)
    plt.title('Watts Strogatz Comparison for a network of n=100 nodes\n on 1000 attempts', fontsize=FT)
    handles, labels = plt.gca().get_legend_handles_labels()
    legend_columns = 2 if len(labels) > 13 else 1
    if legend_columns == 2:
        left_labels = [label for i, label in enumerate(labels) if i % 2 == 0]
        right_labels = [label for i, label in enumerate(labels) if i % 2 == 1]
        left_handles = [handle for i, handle in enumerate(handles) if i % 2 == 0]
        right_handles = [handle for i, handle in enumerate(handles) if i % 2 == 1]
        final_labels = []
        final_labels.extend(left_labels)
        final_labels.extend(right_labels)
        final_handles = []
        final_handles.extend(left_handles)
        final_handles.extend(right_handles)
        plt.legend(final_handles, final_labels, ncol=legend_columns, fontsize=FT-3)
    else:
        plt.legend(ncol = legend_columns, fontsize=FT-3)
    plt.savefig("img/watts_strogatz.png", dpi=600)
    plt.savefig("img/watts_strogatz.pdf", dpi=600)
    
    
    plt.figure(figsize=(10, 6))

    for i, k in enumerate(ks):
        pca_counts = [res[k][edge_prob][0] for edge_prob in edge_probs]
        pca_percentage = [count / 1000 * 100 for count in pca_counts]
        dolev_counts = [res[k][edge_prob][1] for edge_prob in edge_probs]
        dolev_percentage = [count / 1000 * 100 for count in dolev_counts]

        plt.plot(edge_probs, dolev_percentage, label=f'Dolev k={k}', color=dolev_colors[i])
        plt.fill_between(edge_probs, pca_ci_lower, pca_ci_upper, color=pca_colors[i], alpha=0.15)
    
    
    plt.xlabel('rewiring probability (p)', fontsize=FT)
    plt.xticks([round(i/100, 2) for i in range(0, 51, 10)], fontsize=FT-4)
    plt.ylabel('percentage of networks that are\n connected out of 1000 attempts', fontsize=FT)
    plt.ylim(top=110)
    plt.yticks([0, 20, 40, 60, 80, 100], fontsize=FT-4)
    plt.title('[DOLEV] Watts Strogatz Comparison for a network of n=100 nodes\n and varying rewiring probabilities on 1000 attempts', fontsize=FT)
    plt.legend(fontsize=FT-3)
    plt.savefig("img/watts_strogatz_dolev.png", dpi=600)
    plt.savefig("img/watts_strogatz_dolev.pdf", dpi=600)
    
    
    plt.figure(figsize=(10, 6))

    for i, k in enumerate(ks):
        pca_counts = [res[k][edge_prob][0] for edge_prob in edge_probs]
        pca_percentage = [count / 1000 * 100 for count in pca_counts]
        dolev_counts = [res[k][edge_prob][1] for edge_prob in edge_probs]
        dolev_percentage = [count / 1000 * 100 for count in dolev_counts]

        plt.plot(edge_probs, pca_percentage, label=f'PCA k={k}', color=pca_colors[i])
        plt.fill_between(edge_probs, dolev_ci_lower, dolev_ci_upper, color=dolev_colors[i], alpha=0.15)
    
    
    plt.xlabel('rewiring probability (p)', fontsize=FT)
    plt.xticks([round(i/100, 2) for i in range(0, 51, 10)], fontsize=FT-4)
    plt.ylabel('percentage of networks that are\n connected out of 1000 attempts', fontsize=FT)
    plt.ylim(top=110)
    plt.yticks([0, 20, 40, 60, 80, 100], fontsize=FT-4)
    plt.title('[PCA] Watts Strogatz Comparison for a network of n=100 nodes\n on 1000 attempts', fontsize=FT)
    plt.legend(fontsize=FT-3)
    plt.savefig("img/watts_strogatz_pca.png", dpi=600)
    plt.savefig("img/watts_strogatz_pca.pdf", dpi=600)



if __name__ == "__main__":
    watts_strogatz_plot()
    """ n, min_k, max_k, attempts, min_edge_prob, max_edge_prob, max_workers = load_settings()
    
    for k in range(min_k, max_k + 1):
        
        edges_prob = get_remaining_tries(k, attempts, min_edge_prob, max_edge_prob)
        print(f"[watts_strogatz] Remaining edge probabilities for k={k}: {edges_prob}", flush=True)
        if edges_prob == []:
            print(f"[watts_strogatz] All edge probabilities have been processed for k={k}. No remaining tries.", flush=True)
            continue

        manager = Manager()
        progress_counter = manager.Value('i', 0)
        progress_lock = manager.Lock()
        stop_flag = manager.Value('b', False)
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            total_attempts = len(edges_prob) * attempts
            future_to_prob = {}
            for edge_prob in edges_prob:
                clear_directory(DIR_PATH / f"pca_{n}_{k}_{edge_prob:.2f}")
                clear_directory(DIR_PATH / f"dolev_{n}_{k}_{edge_prob:.2f}")
                future = executor.submit(generate_networks, n, k, edge_prob, attempts=attempts, progress_counter=progress_counter, progress_lock=progress_lock, total_attempts=total_attempts, stop_flag=stop_flag)
                future_to_prob[future] = edge_prob

            try:
                for future in as_completed(future_to_prob):
                    edge_prob = future_to_prob[future]
                    try:
                        edge_prob, pca_count, dolev_count = future.result()
                        print("saving results to file...", flush=True)
                        append_result_to_file(n, k, edge_prob, pca_count, dolev_count, attempts)
                    except Exception as exc:
                        print(f"[main] Edge probability {edge_prob:.2f} generated an exception: {exc}", flush=True)
            except KeyboardInterrupt:
                stop_flag.value = True
                print("\nCtrl+C received, shutting down threads...", flush=True)
                executor.shutdown(wait=False, cancel_futures=True)
                raise """