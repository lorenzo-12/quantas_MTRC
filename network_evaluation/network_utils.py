import pathlib 
import colorama
import networkx as nx
import json
import os 
import matplotlib.pyplot as plt
import random
from statsmodels.stats.proportion import proportion_confint
from collections import deque

FT = 18

RED = colorama.Fore.RED
GREEN = colorama.Fore.GREEN
BLUE = colorama.Fore.BLUE
RESET = colorama.Fore.RESET

class Node:
    def __init__(self, id):
        self.id = id
        self.neighbors = set()
        self.is_byzantine = False
    
    def add_neighbor(self, neighbor):
        self.neighbors.add(neighbor)
    
    def remove_neighbor(self, neighbor):
        if neighbor in self.neighbors:
            self.neighbors.discard(neighbor)
            neighbor.remove_neighbor(self)
    
    def get_neighbors(self):
        return self.neighbors
    
    def set_node_byzantine(self) -> None:
        self.is_byzantine = True
    
    def to_dict(self):
        return {
            "id": self.id,
            "neighbors": [neighbor.id for neighbor in self.neighbors],
            "is_byzantine": self.is_byzantine
        }
    
    def __hash__(self):
        return hash(self.id)

    def __eq__(self, value):
        if value is None:
            return False
        if isinstance(value, self.__class__):
            return self.id == value.id
        return False
        

class Network:
    def __init__(self):
        self.nodes = {}
    
    def get_node(self, node_id):
        if node_id in self.nodes:
            return self.nodes[node_id]
        return None
        
    def add_node(self, node_id):
        node = Node(node_id)
        self.nodes[node_id] = node
        return node
    
    def add_edge(self, node1: Node, node2: Node):
        if node1.id not in self.nodes:
            node1 = self.add_node(node1.id)
        if node2.id not in self.nodes:
            node2 = self.add_node(node2.id)        
        node1.add_neighbor(node2)
        node2.add_neighbor(node1)
    
    def remove_edge(self, node1: Node, node2: Node):
        
        if node1.id not in self.nodes or node2.id not in self.nodes:
            return
        node1.remove_neighbor(node2)
        node2.remove_neighbor(node1)
    
    def get_edges(self):
        edges = set()
        for node in self.nodes.values():
            for neighbor in node.get_neighbors():
                if (neighbor, node) not in edges and (node, neighbor) not in edges:
                    edges.add((node, neighbor))
        return edges

    def check_k_connectivity(self, k: int) -> bool:
        G = network_to_networkx(self)
        dolev_k = nx.node_connectivity(G)
        return dolev_k >= k

    def can_remove_edge(self, node1_id: str, node2_id: str, k: int) -> bool:
        node1 = self.get_node(node1_id)
        node2 = self.get_node(node2_id)
        
        if node1 is None or node2 is None:
            return False
        
        if node2 not in node1.get_neighbors() or node1 not in node2.get_neighbors():
            return False
        
        self.remove_edge(node1, node2)
        dolev_k = nx.node_connectivity(network_to_networkx(self))
        self.add_edge(node1, node2)
        
        return True
    
    def reset(self) -> None:
        for node in self.nodes.values():
            node.is_byzantine = False
    
    def set_byzantine_nodes(self, t: int):
        self.reset()
        nodes_list = [node.id for node in self.nodes.values()]
        nodes_list.remove(0)
        random.shuffle(nodes_list)
        for i in range(t):
            self.nodes[nodes_list[i]].set_node_byzantine()
        
    def get_stats(self):
        num_nodes = len(self.nodes)
        num_edges = sum(len(node.get_neighbors()) for node in self.nodes.values()) // 2
        avg_neighbors = float((2 * num_edges)) / num_nodes if num_nodes > 0 else 0
        avg_neighbors = round(avg_neighbors, 2)
        max_neighbors = max(len(node.get_neighbors()) for node in self.nodes.values()) if num_nodes > 0 else 0
        num_byzantine = sum(1 for node in self.nodes.values() if node.is_byzantine)
        return num_nodes, num_edges, avg_neighbors, max_neighbors, num_byzantine

    def to_dict(self):
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()]
        }
    
        


class PCANode(Node):
    def __init__(self, id):
        super().__init__(id)
        self.enqueued = False
        self.count = 0
        self.count_byzantine_neighbors = 0

    def increment(self) -> None:
        self.count += 1
        
    def set_node_byzantine(self) -> None:
        self.is_byzantine = True
        for neighbor in self.get_neighbors():
            neighbor.count_byzantine_neighbors += 1 
    
    def can_be_byzantine(self, k) -> bool:
        # already byzantine
        if self.is_byzantine:
            return False
        
        # if any correct neighbor has already k byzantine neighbors, then this node cannot be byzantine
        for neighbor in self.get_neighbors():
            if neighbor.is_byzantine:
                continue
            if neighbor.count_byzantine_neighbors >= k:
                return False
        return True
        

class PCANetwork(Network):
    def __init__(self):
        super().__init__()
    
    def add_node(self, node_id) -> PCANode:
        node = PCANode(node_id)
        self.nodes[node_id] = node
        return node


    def reset(self) -> None:
        super().reset()
        for node in self.nodes.values():
            node.count = 0
            node.enqueued = False
            node.count_byzantine_neighbors = 0

    def check_k_level_ordering_source(self, source: PCANode, k: int) -> bool:
        self.reset()
        
        queue = deque([source])
        source.enqueued = True

        for neighbor in source.get_neighbors():
            queue.append(neighbor)
            neighbor.enqueued = True
        
        while queue:
            current_node = queue.popleft()
            
            for neighbor in current_node.get_neighbors():
                neighbor.increment()
                
                if (neighbor.count >= k) and (not neighbor.enqueued):
                    neighbor.enqueued = True
                    queue.append(neighbor)
        
        for node in self.nodes.values():
            if not node.enqueued:
                return False
        return True


    def check_k_level_ordering(self, k: int) -> bool:
        for node_id in self.nodes:
            if not self.check_k_level_ordering_source(self.nodes[node_id], k):
                #print(f"{RED}network not a {k}-level-ordering{RESET}")
                return False
        #print(f"{GREEN}network is a {k}-level-ordering{RESET}")
        return True
    
    def can_remove_edge(self, node1_id: str, node2_id: str, k: int) -> bool:
        node1 = self.get_node(node1_id)
        node2 = self.get_node(node2_id)
        
        if node1 is None or node2 is None:
            return False
        if node2 not in node1.get_neighbors() or node1 not in node2.get_neighbors():
            return False
        
        self.remove_edge(node1, node2)
        is_k_level_ordering = self.check_k_level_ordering(k)
        self.add_edge(node1, node2)
        
        return is_k_level_ordering
    
    def set_byzantine_nodes(self, k: int):
        self.reset()
        total_byz = 0
        nodes_list = sorted(self.nodes.values(), key=lambda node: len(node.get_neighbors()), reverse=True)
        for node in nodes_list:
            if node.id == 0:
                continue
            if node.can_be_byzantine(k):
                node.set_node_byzantine()
                total_byz += 1
        return total_byz
    
    def get_max_edge_removal(self, k: int, edge_list: list) -> int:
        edge_removed = 0
        step = 1000
        i = 0
        
        while True:
            
            if i + step > len(edge_list):
                step = len(edge_list) - i
            #print(f"step {step}: Trying to remove edges from index {i} to {i+step-1}")
            for j in range(i, i+step):
                node1_id, node2_id = edge_list[j]
                self.remove_edge(self.get_node(node1_id), self.get_node(node2_id))
            if self.check_k_level_ordering(k):
                edge_removed += step
                i += step
            else:
                for j in range(i, i+step):
                    node1_id, node2_id = edge_list[j]
                    self.add_edge(self.get_node(node1_id), self.get_node(node2_id))
                step = int(step / 2)
                if step <= 20:
                    break 
        
        #print(f"Batch edge removal done. Total edges removed: {edge_removed}. Now trying to remove remaining edges one by one.")
        while True:
            #print(f"Trying to remove edge at index {i}")
            self.remove_edge(self.get_node(edge_list[i][0]), self.get_node(edge_list[i][1]))
            if self.check_k_level_ordering(k):
                edge_removed += 1
                i += 1
            else:
                self.add_edge(self.get_node(edge_list[i][0]), self.get_node(edge_list[i][1]))
                break
        return edge_removed
        
    
    

    def get_stats(self):
        num_nodes, num_edges, avg_neighbors, max_neighbors, num_byzantine = super().get_stats()
        x = [node.count_byzantine_neighbors for node in self.nodes.values()]
        avg_byzantine_neighbors = round(sum(x) / len(x), 2) if len(x) > 0 else 0
        return num_nodes, num_edges, avg_neighbors, max_neighbors, num_byzantine, avg_byzantine_neighbors



def get_max_edge_removal(network: nx.Graph, k: int, edge_list: list):
    edge_removed = 0
    i = 0
    step = 1000
    
    # try to remove edges in batches of "step" until we cannot remove anymore, 
    # then we will try to remove the remaining edges one by one
    while True:
        
        if i + step > len(edge_list):
                step = len(edge_list) - i
                
        #print(f"step {step}: Trying to remove edges from index {i} to {i+step-1}")
        for j in range(i, i+step):
            network.remove_edge(edge_list[j][0], edge_list[j][1])
        if nx.node_connectivity(network) >= k:
            edge_removed += step
            i += step
        else:
            for j in range(i, i+step):
                network.add_edge(edge_list[j][0], edge_list[j][1])
            step = int(step / 2)
            if step <= 20:
                break 
            
    #print(f"Batch edge removal done. Total edges removed: {edge_removed}. Now trying to remove remaining edges one by one.")
    # try to remove the remaining edges one by one    
    while True:
        #print(f"Trying to remove edge at index {i}")
        network.remove_edge(edge_list[i][0], edge_list[i][1])
        if nx.node_connectivity(network) >= k:
            edge_removed += 1
            i += 1
        else:
            network.add_edge(edge_list[i][0], edge_list[i][1])
            break
    return network, edge_removed
        



def networkx_to_network(netx_graph, network_type=Network):
    network = network_type()
    for node in netx_graph.nodes():
        network.add_node(node)
    for edge in netx_graph.edges():
        node1_id, node2_id = edge
        node1 = network.get_node(node1_id)
        node2 = network.get_node(node2_id)
        network.add_edge(node1, node2)
    return network

def network_to_networkx(network):
    G = nx.Graph()
    for node in network.nodes.values():
        G.add_node(node.id)
    for node in network.nodes.values():
        for neighbor in node.get_neighbors():
            if not G.has_edge(node.id, neighbor.id):
                G.add_edge(node.id, neighbor.id)
    return G

def json_to_network(json_file, network_type=Network):
    with open(json_file, "r") as f:
        data = json.load(f)
    
    network = network_type()
    for node_data in data["nodes"]:
        node_id = node_data["id"]
        n = network.add_node(node_id)
        n.set_node_byzantine() if node_data.get("is_byzantine", False) else None
    
    for node_data in data["nodes"]:
        node_id = node_data["id"]
        neighbors = node_data["neighbors"]
        for neighbor_id in neighbors:
            node1 = network.get_node(node_id)
            node2 = network.get_node(neighbor_id)
            network.add_edge(node1, node2)
    
    return network


def save_network(network, file_path, file_name):
    data = network.to_dict()
    
    # if file_path does not exist, create it
    if not os.path.exists(file_path):
        os.makedirs(file_path)
        
    with open(file_path / f"{file_name}.json", "w") as f:
        json.dump(data, f, indent=4)
    

def wilson_ci(successes, trials, alpha=0.05):
    low, high = proportion_confint(successes, trials, alpha=alpha, method="wilson")
    return low, high


def print_results(list_results, n, k, trials=10000, alpha=0.05):
    prob = [result[0] for result in list_results]
    num_pca = [result[1] for result in list_results]
    num_dolev = [result[2] for result in list_results]

    pca_low = []
    pca_high = []
    dolev_low = []
    dolev_high = []

    for p, pca_count, dolev_count in zip(prob, num_pca, num_dolev):
        pca_l, pca_h = wilson_ci(pca_count, trials, alpha=alpha)
        dolev_l, dolev_h = wilson_ci(dolev_count, trials, alpha=alpha)

        pca_low.append(pca_l * trials)
        pca_high.append(pca_h * trials)
        dolev_low.append(dolev_l * trials)
        dolev_high.append(dolev_h * trials)

    plt.figure(figsize=(20, 6))
    plt.plot(prob, num_pca, color="blue", marker="o", label="PCA")
    plt.plot(prob, num_dolev, color="red", marker="o", label="Dolev")

    plt.fill_between(prob, pca_low, pca_high, color="blue", alpha=0.15, label="PCA 95% CI")
    plt.fill_between(prob, dolev_low, dolev_high, color="red", alpha=0.15, label="Dolev 95% CI")

    plt.xlabel("Probability")
    plt.ylabel(f"Good results out of {trials}")
    plt.title(f"Good results vs probability at generating a network with n={n}, k={k} with {trials} attempts per edge probability")
    plt.xticks(prob, [f"{p:.2f}" for p in prob])
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"results_n{n}_k{k}.png")
    
    
    

        
    