import csv
import os 
import json
import pathlib


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
     

def append_result_to_file(results_file, edge_prob, pca_count, dolev_count, tries):
    file_exists = os.path.exists(results_file)
    with open(results_file, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["edge_prob", "pca_count", "dolev_count", "attempts_per_edge_prob"])
        writer.writerow([f"{edge_prob:.2f}", pca_count, dolev_count, tries])    

def load_settings(file: str = "settings/settings.json"):
    
    with open(file, "r") as f:
        settings = json.load(f)
    
    network_type = settings.get("network", "erdos_renyi")
    n = settings.get("n", 100)
    t = settings.get("t", 4)
    min_edge_prob = settings.get("min_edge_prob", 0.01)
    max_edge_prob = settings.get("max_edge_prob", 1.00)
    attempts_per_edge_prob = settings.get("attempts_per_edge_prob", 1000)
    thread_pool_size = settings.get("thread_pool_size", 1)
    results_file = pathlib.Path(__file__).parent / "results" / f"{network_type}.csv"
    nets_dir = pathlib.Path(__file__).parent / "nets" / network_type
    return network_type, n, t, min_edge_prob, max_edge_prob, attempts_per_edge_prob, thread_pool_size, results_file, nets_dir

def get_remaining_tries(results_file, attempts_per_edge_prob, min_edge_prob, max_edge_prob):
    remaining_tries = [round(i/100, 2) for i in range(int(min_edge_prob * 100), int(max_edge_prob * 100) + 1)]
    
    if not os.path.exists(results_file):
        return remaining_tries
    
    lines = open(results_file, "r").readlines()
    for line in lines[1:]:  # Skip header
        edge_prob, pca_count, dolev_count, attempt = line.strip().split(",")
        edge_prob = round(float(edge_prob), 2)
        attempt = int(attempt)
        if attempt == attempts_per_edge_prob and edge_prob in remaining_tries:
            remaining_tries.remove(edge_prob)
    
    return remaining_tries

def order_results_watts_strogatz():
    input_file = "results/watts_strogatz.csv"
    output_file = "results/watts_strogatz_ordered.csv"

    with open(input_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # sort by:
    # 1. n
    # 2. k
    # 3. edge_prob
    rows.sort(key=lambda row: (int(row[0]), int(row[1]), float(row[2])))

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
        
def order_results_random_regular():
    input_file = "results/random_regular.csv"
    output_file = "results/random_regular_ordered.csv"

    with open(input_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # sort by:
    # 1. n
    # 2. k
    # 3. d
    rows.sort(key=lambda row: (int(row[0]), int(row[1]), float(row[2])))

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        

def order_results_erdos_renyi():
    input_file = "results/erdos_renyi.csv"
    output_file = "results/erdos_renyi_ordered.csv"
    
    with open(input_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # sort by:
    # 1. n
    # 2. k
    # 3. edge_prob
    rows.sort(key=lambda row: (int(row[0]), int(row[1]), float(row[2])))

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)


def order_results_edge_remover():
    input_file = "results/edge_remover.csv"
    output_file = "results/edge_remover_ordered.csv"
    
    with open(input_file, "r", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)

    # sort by:
    # 1. n
    # 2. k
    rows.sort(key=lambda row: (int(row[0]), int(row[1])))

    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
        
        
        
if __name__ == "__main__":
    order_results_edge_remover()
    order_results_erdos_renyi()
    order_results_random_regular()
    order_results_watts_strogatz()