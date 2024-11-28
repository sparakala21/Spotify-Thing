import json
import networkx as nx
from networkx.algorithms import community
import matplotlib.pyplot as plt
import re
import random


def create_edge_list(json_data, subset):
    edge_list = []
    for item in json_data:
        i=0
        for main_artist, related_artists in item.items():
            for related_artist in related_artists:
                edge_list.append((main_artist, related_artist))
            i+=1
            if i>=subset:
                return edge_list
    return edge_list


def create_network_from_json(json_data, subset=100, labels=False):
    # Create empty graph
    json_data = json_data[:subset]
    G = nx.Graph()
    i=0
    # Add edges from JSON
    breakcondition = False
    for item in json_data:
        for main_artist, related_artists in item.items():
            for related_artist in related_artists:
                i+=1
                G.add_edge(main_artist, related_artist)
    print(i)
    # Create layout
    pos = nx.spring_layout(G, k=1, iterations=50)
    
    # Setup plot
    plt.figure(figsize=(12, 12))
    
    # Draw network
    nx.draw_networkx_nodes(G, pos, node_size=100)
    nx.draw_networkx_edges(G, pos)
    if labels:
        nx.draw_networkx_labels(G, pos, font_size=6)
    
    plt.title("Artist Network")
    plt.axis('off')
    plt.tight_layout()
    
    return G, plt
G = nx.DiGraph()
liked = set()
unknown = set()
year = 2018
subset = 50
with open("../data/artist_adjacency_list_{}.json".format(str(year)), "r") as jsonfile:
    artist_list = json.load(jsonfile)

    G, plt = create_network_from_json(artist_list, subset)
    communities = community.louvain_communities(G)

    # Color nodes by community
    colors = ['#%06X' % random.randint(0, 0xFFFFFF) for _ in range(len(communities))]
    node_colors = []
    node_to_community = {}

    for i, com in enumerate(communities):
        for node in com:
            node_to_community[node] = i
            
    for node in G.nodes():
        node_colors.append(colors[node_to_community[node]])

    # Draw with community colors
    pos = nx.spring_layout(G, k=1, iterations=50)
    plt.figure(figsize=(12, 12))
    nx.draw_networkx_nodes(G, pos, node_size=100, node_color=node_colors)
    nx.draw_networkx_edges(G, pos)
    plt.title("Artist Network with Communities")
    plt.axis('off')

    plt.savefig("../results/community/{}_{}.png".format(year, subset))
    print(f"Number of communities: {len(communities)}")
    print(f"Community sizes: {[len(c) for c in communities]}") 
