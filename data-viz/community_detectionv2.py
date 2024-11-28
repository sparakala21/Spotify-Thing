import json
import networkx as nx
from networkx.algorithms import community
import matplotlib.pyplot as plt
import re
import random
import numpy as np

def sanitize_name(name):
    return re.sub(r'[^A-Za-z0-9\s]', '', name)

def create_adjacency_list(json_data, subset=100, labels=False):
    id_to_name = dict()
    popularity_dict = dict()
    adj_list = dict()
    id_to_genres = dict()
    i=0
    for artist_id, data in json_data.items():
        current_artist = data['artist']['id']
        id_to_name[current_artist] = data['artist']['name']
        popularity_dict[current_artist] = data['artist']['popularity']
        id_to_genres[current_artist] = data['artist']['genres']
        friends = []

        for artist in data['related_artists']:
            friends.append(artist['id'])
            popularity_dict[artist['id']] = artist['popularity']
            id_to_name[artist['id']] = artist['name']
            id_to_genres[artist['id']] = artist['genres']
        adj_list[current_artist] = friends
        i+=1
        if i>=100:
            break
    return adj_list, id_to_name, popularity_dict, id_to_genres

def create_graph(adj_list, id_to_name, popularity_dict, artists_I_like):
    G = nx.Graph()
    for main_artist, related_artists in adj_list.items():
        for r in related_artists:
            G.add_edge(main_artist, r)
    min_size = min(popularity_dict.values())
    max_size = max(popularity_dict.values())
    node_sizes = []
    for node in G.nodes():
        size = popularity_dict.get(node)
        node_sizes.append((size-min_size) * 25)
    
    communities = community.louvain_communities(G)
    colors = ['#%06X' % random.randint(0, 0xFFFFFF) for _ in range(len(communities))]
    node_colors = []
    node_to_community = {}
    
    # Find most popular artist per community
    community_leaders = {}
    for i, com in enumerate(communities):
        max_popularity = -1
        leader = None
        for node in com:
            pop = popularity_dict.get(node)
            if pop > max_popularity:
                max_popularity = pop
                leader = node
        community_leaders[i] = leader

    for i, com in enumerate(communities):
        for node in com:
            node_to_community[node] = i
            
    for node in G.nodes():
        node_colors.append(colors[node_to_community[node]])

    # Initial layout with increased spacing
    pos_initial = nx.spring_layout(G, k=7)  # Increased k for even more initial spread
    pos = pos_initial.copy()

    # Calculate community centers and sizes
    community_centers = {}
    community_sizes = {}
    for i, com in enumerate(communities):
        center = np.array([0.0, 0.0])
        for node in com:
            center += pos[node]
        center /= len(com)
        community_centers[i] = center
        community_sizes[i] = len(com)

    # Modified layout algorithm with stronger node repulsion within communities
    for _ in range(100):
        # Update positions based on community centers and node repulsion
        for node in G.nodes():
            comm = node_to_community[node]
            current_pos = np.array(pos[node])
            
            # Attraction to own community center (weakened)
            center_pull = community_centers[comm] - current_pos
            
            # Repulsion from other community centers
            repulsion_from_communities = np.array([0.0, 0.0])
            for other_comm, other_center in community_centers.items():
                if other_comm != comm:
                    diff = current_pos - other_center
                    dist = max(np.linalg.norm(diff), 0.1)
                    repulsion_from_communities += diff / (dist ** 2) * community_sizes[other_comm]
            
            # Repulsion from other nodes in same community (strengthened)
            repulsion_from_nodes = np.array([0.0, 0.0])
            for other_node in G.nodes():
                if node != other_node and node_to_community[other_node] == comm:
                    diff = current_pos - pos[other_node]
                    dist = max(np.linalg.norm(diff), 0.01)  # Smaller minimum distance
                    repulsion_from_nodes += diff / (dist ** 2.5)  # Stronger repulsion
            
            # Update position with adjusted weights
            pos[node] = (current_pos + 
                        0.05 * center_pull +  # Reduced center attraction
                        0.2 * repulsion_from_communities + 
                        0.15 * repulsion_from_nodes)  # Increased node repulsion
            
        # Update community centers
        for i, com in enumerate(communities):
            center = np.array([0.0, 0.0])
            for node in com:
                center += pos[node]
            community_centers[i] = center / len(com)

    plt.figure(figsize=(30, 30))
    
    # Draw regular nodes
    regular_nodes = [node for node in G.nodes() if node not in artists_I_like]
    regular_sizes = [node_sizes[i] for i, node in enumerate(G.nodes()) if node not in artists_I_like]
    regular_colors = [node_colors[i] for i, node in enumerate(G.nodes()) if node not in artists_I_like]
    
    nx.draw_networkx_nodes(G, pos, 
                          nodelist=regular_nodes,
                          node_size=regular_sizes, 
                          node_color=regular_colors, 
                          edgecolors='black', 
                          linewidths=1)
    
    # Draw highlighted nodes (favorites)
    favorite_nodes = [node for node in G.nodes() if node in artists_I_like]
    favorite_sizes = [node_sizes[i] for i, node in enumerate(G.nodes()) if node in artists_I_like]
    favorite_colors = [node_colors[i] for i, node in enumerate(G.nodes()) if node in artists_I_like]
    
    nx.draw_networkx_nodes(G, pos, 
                          nodelist=favorite_nodes,
                          node_size=favorite_sizes, 
                          node_color=favorite_colors, 
                          edgecolors='#FFD700',  # Gold border
                          linewidths=3)           # Thicker border
    
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    
    # Add labels for community leaders and favorite artists
    labels = {node: sanitize_name(id_to_name[node]) if (node in artists_I_like) else '' 
             for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=24)
    
    plt.title("Artist Network with Communities (Node Size = Popularity)\nFavorite Artists Highlighted in Gold", fontsize=28)
    plt.axis('off')
    
    return G, plt, communities
def analyze_community_genres(communities, id_to_name, popularity_dict, id_to_genres):
    community_analysis = []
    
    for i, community in enumerate(communities):
        # Collect all genres in this community
        genre_count = {}
        community_size = len(community)
        
        # Count occurrences of each genre
        for artist_id in community:
            for genre in id_to_genres[artist_id]:
                genre_count[genre] = genre_count.get(genre, 0) + 1
        
        # Calculate genre prevalence (percentage of community members with each genre)
        genre_prevalence = {genre: count/community_size * 100 
                          for genre, count in genre_count.items()}
        
        # Sort genres by prevalence
        common_genres = sorted(genre_prevalence.items(), 
                             key=lambda x: x[1], 
                             reverse=True)
        
        # Filter for genres that appear in at least 30% of the community
        significant_genres = [genre for genre, prev in common_genres if prev >= 30]
        
        community_info = {
            'size': community_size,
            'common_genres': significant_genres,
            'artists': [{
                'name': id_to_name[id],
                'popularity': popularity_dict[id],
                'genres': id_to_genres[id]
            } for id in community]
        }
        
        community_analysis.append(community_info)
    
    # Print analysis
    print(f"\nNumber of communities: {len(communities)}")
    print("\nCommunity Analysis:")
    for i, comm in enumerate(community_analysis):
        print(f"\nCommunity {i+1} (Size: {comm['size']})")
        print(f"Common Genres: {', '.join(comm['common_genres'])}")
        print("Top Artists:")
        # Sort artists by popularity and show top 3
        sorted_artists = sorted(comm['artists'], 
                              key=lambda x: x['popularity'], 
                              reverse=True)[:3]
        for artist in sorted_artists:
            print(f"  - {artist['name']} (Popularity: {artist['popularity']})")

artists_I_like = []

with open("../data/artist_adjacency_list.json") as jsonfile:
    a = json.load(jsonfile)
    for artist in a:
        artists_I_like.append(list(artist.keys())[0])

genres = ['edm', 'filmi', 'hip-hop', 'jazz', 'pop']
for genre in genres:
    with open("../data/something/{}.json".format(genre), "r") as jsonfile:
        artist_dict = json.load(jsonfile)
        adj_list, id_to_name, popularity_dict, id_to_genres = create_adjacency_list(artist_dict, subset=1000)
        G, plt, communities = create_graph(adj_list, id_to_name, popularity_dict, artists_I_like)

        plt.savefig("../results/communityv2/{}.png".format(genre), dpi=300, bbox_inches='tight')
        
        # Call the new analysis function
        analyze_community_genres(communities, id_to_name, popularity_dict, id_to_genres)
        # print([[{
        #     'name': id_to_name[id], 
        #     'popularity': popularity_dict[id], 
        #     'genres': id_to_genres} for id in list(community)] for community in communities])