import networkx as nx
from network_utils import *
import time 

n = 100
k = 10
G = nx.complete_graph(n)


list_edges = list(G.edges())
random.shuffle(list_edges)

pca_network = networkx_to_network(G, PCANetwork)


start = time.time()
net, edge_removed_dolev = get_max_edge_removal(G.copy(), k, list_edges)
end = time.time()
print(f"Dolev edge removal took {end - start:.2f} seconds")

print("\n\n\n")
start = time.time()
edge_removed_pca = pca_network.get_max_edge_removal(k, list_edges)
end = time.time()
print(f"PCA edge removal took {end - start:.2f} seconds")
