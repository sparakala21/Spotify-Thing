import json
import networkx as nx
import matplotlib.pyplot as plt
import re

G = nx.DiGraph()
liked = set()
unknown = set()
year = 2017
with open("../data/artist_adjacency_list_{}.json".format(str(year)), "r") as jsonfile:
    artist_list = json.load(jsonfile)
    print(artist_list)
    i=0

    for item in artist_list:
        #item is a dictionary
        for artist, friends in item.items():
            print(artist)

            for friend in friends:
                G.add_edge(artist, friend)
                liked.add(artist)
                if friend not in liked and not in unknown:
                    unknown.add(friend)
pos = nx.spring_layout(G)
plt.figure(figsize=(12, 12))

# Draw nodes from earliest to latest to ensure layering
nx.draw_networkx_nodes(G, pos, nodelist=list(liked & G.nodes), node_size=200, node_color="#ff0000", label="artists i knew in 2017")  # Red
nx.draw_networkx_nodes(G, pos, nodelist=list(unknown & G.nodes), node_size=200, node_color="#00ff00", label="artists i didnt know in 2017")  # Red
# Draw all edges
nx.draw_networkx_edges(G, pos, arrowsize=20, arrowstyle="-", edge_color="gray")
# nx.draw_networkx_labels(G, pos, font_size=8)
# Title, legend, and display
plt.title("Combined Artist Friendship Graph (2018, 2019, & 2020) with Weighted Edges")
plt.legend()
plt.axis("off")  # Turn off the axis
plt.savefig("../results/{}_id_only.png".format(year))
