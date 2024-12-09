import json
import networkx as nx
import matplotlib.pyplot as plt
import re

# Function to sanitize artist names by removing special characters
def sanitize_name(name):
    return re.sub(r'[^A-Za-z0-9\s]', '', name)

# Create a new directed graph
G = nx.DiGraph()

# Sets to track nodes based on year
nodes = set()
limit = 20
year = 2018
# Load data for each year and add edges with year-based weights
with open("../data/artists_and_friends_{}.json".format(str(2021)), "r") as jsonfile:
    artist_list = json.load(jsonfile)
    i=0
    for artist, friends in artist_list.items():
        sanitized_artist = sanitize_name(artist)
        nodes.add(sanitized_artist)  # Mark node based on year
        for friend in friends:
            if len(friend) == 22:  # Skip artists without known names
                continue
            sanitized_friend = sanitize_name(friend)
            
            G.add_edge(sanitized_artist, sanitized_friend)
            nodes.add(sanitized_friend)  # Mark friend based on year
        i+=1
        if i>limit:
            break

pos = nx.spring_layout(G)
# Filter out nodes without positions
# G_with_pos = G.subgraph(pos.keys())

# Plotting
plt.figure(figsize=(12, 12))

# Draw nodes from earliest to latest to ensure layering
nx.draw_networkx_nodes(G, pos, nodelist=list(nodes & G.nodes), node_size=200, node_color="#ff0000", label="2018 Artists")  # Red
print(len(nodes))
# Draw all edges
nx.draw_networkx_edges(G, pos, arrowsize=20, edge_color="gray")
nx.draw_networkx_labels(G, pos, font_size=8)
# Title, legend, and display
plt.title("Combined Artist Friendship Graph (2018, 2019, & 2020) with Weighted Edges")
plt.legend()
plt.axis("off")  # Turn off the axis
plt.savefig("../results/{}_subset_{}.png".format(year, limit))
