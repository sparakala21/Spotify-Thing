import json
import networkx as nx
from networkx.algorithms import community
import matplotlib.pyplot as plt
import re
import random
import numpy as np
import csv
import pandas as pd
from prediction import predict_next_artists

def sanitize_name(name):
    return re.sub(r'[^A-Za-z0-9\s]', '', name)

def create_adjacency_list(json_data, subset=100):
    id_to_name = dict()
    popularity_dict = dict()
    adj_list = dict()
    id_to_genres = dict()
    i = 0
    
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
        i += 1
        if i >= subset:
            break
            
    return adj_list, id_to_name, popularity_dict, id_to_genres

def create_graph(adj_list, id_to_name, popularity_dict, artists_I_like):
    # Create graph
    G = nx.Graph()
    for main_artist, related_artists in adj_list.items():
        for r in related_artists:
            G.add_edge(main_artist, r)
            
    # Calculate node sizes based on popularity
    min_size = min(popularity_dict.values())
    max_size = max(popularity_dict.values())
    node_sizes = [(popularity_dict.get(node)-min_size) * 25 for node in G.nodes()]
    
    # Detect communities
    communities = community.louvain_communities(G)
    colors = ['#%06X' % random.randint(0, 0xFFFFFF) for _ in range(len(communities))]
    
    # Map nodes to communities
    node_to_community = {}
    for i, com in enumerate(communities):
        for node in com:
            node_to_community[node] = i
            
    node_colors = [colors[node_to_community[node]] for node in G.nodes()]
    
    # Calculate layout
    pos_initial = nx.spring_layout(G, k=7)
    pos = pos_initial.copy()
    
    # Calculate community centers and sizes
    community_centers = {}
    community_sizes = {}
    for i, com in enumerate(communities):
        center = np.mean([pos[node] for node in com], axis=0)
        community_centers[i] = center
        community_sizes[i] = len(com)
    
    # Optimize layout
    for _ in range(100):
        for node in G.nodes():
            comm = node_to_community[node]
            current_pos = np.array(pos[node])
            
            # Forces
            center_pull = community_centers[comm] - current_pos
            
            repulsion_from_communities = np.zeros(2)
            for other_comm, other_center in community_centers.items():
                if other_comm != comm:
                    diff = current_pos - other_center
                    dist = max(np.linalg.norm(diff), 0.1)
                    repulsion_from_communities += diff / (dist ** 2) * community_sizes[other_comm]
            
            repulsion_from_nodes = np.zeros(2)
            for other_node in G.nodes():
                if node != other_node and node_to_community[other_node] == comm:
                    diff = current_pos - pos[other_node]
                    dist = max(np.linalg.norm(diff), 0.01)
                    repulsion_from_nodes += diff / (dist ** 2.5)
            
            # Update position
            pos[node] = (current_pos + 
                        0.05 * center_pull +
                        0.2 * repulsion_from_communities +
                        0.15 * repulsion_from_nodes)
        
        # Update centers
        for i, com in enumerate(communities):
            community_centers[i] = np.mean([pos[node] for node in com], axis=0)
    
    return G, communities, pos, node_sizes, node_colors

def visualize_graph(G, pos, communities, node_sizes, node_colors, id_to_name, artists_I_like, recommendations=None):
    plt.figure(figsize=(30, 30))
    
    # Draw regular nodes
    regular_nodes = [node for node in G.nodes() 
                    if node not in artists_I_like and 
                    (recommendations is None or id_to_name[node] not in [r['artist'] for r in recommendations])]
    
    nx.draw_networkx_nodes(G, pos, 
                          nodelist=regular_nodes,
                          node_size=[node_sizes[i] for i, node in enumerate(G.nodes()) if node in regular_nodes],
                          node_color=[node_colors[i] for i, node in enumerate(G.nodes()) if node in regular_nodes],
                          edgecolors='black',
                          linewidths=1)
    
    # Draw favorite artists
    if artists_I_like:
        favorite_nodes = [node for node in G.nodes() if node in artists_I_like]
        nx.draw_networkx_nodes(G, pos,
                             nodelist=favorite_nodes,
                             node_size=[node_sizes[i] for i, node in enumerate(G.nodes()) if node in favorite_nodes],
                             node_color=[node_colors[i] for i, node in enumerate(G.nodes()) if node in favorite_nodes],
                             edgecolors='#FFD700',
                             linewidths=3)
    
    # Draw recommended artists
    if recommendations:
        recommended_nodes = [node for node in G.nodes() 
                           if id_to_name[node] in [r['artist'] for r in recommendations]]
        nx.draw_networkx_nodes(G, pos,
                             nodelist=recommended_nodes,
                             node_size=[node_sizes[i] for i, node in enumerate(G.nodes()) if node in recommended_nodes],
                             node_color=[node_colors[i] for i, node in enumerate(G.nodes()) if node in recommended_nodes],
                             edgecolors='#0000FF',
                             linewidths=8)
    
    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.3)
    
    # Add labels
    labels = {node: sanitize_name(id_to_name[node]) 
             if ((recommendations and id_to_name[node] in [r['artist'] for r in recommendations]))
             else ''
             for node in G.nodes()}
    nx.draw_networkx_labels(G, pos, labels, font_size=24)
    
    title = "Artist Network with Communities (Node Size = Popularity)"
    if artists_I_like:
        title += "\nFavorite Artists Highlighted in Gold"
    if recommendations:
        title += " and Recommendations in Pink"
    plt.title(title, fontsize=28)
    plt.axis('off')
    
    return plt

def write_communities_to_json(communities, id_to_name, popularity_dict, id_to_genres, output_path):
    """
    Write community data to a JSON file with detailed genre analysis.
    
    Parameters:
    communities -- list of community sets containing artist IDs
    id_to_name -- dictionary mapping artist IDs to names
    popularity_dict -- dictionary mapping artist IDs to popularity scores
    id_to_genres -- dictionary mapping artist IDs to genre lists
    output_path -- path where JSON file will be saved
    """
    result = []
    
    for community_id, community in enumerate(communities):
        # Initialize community data
        genre_count = {}
        community_size = len(community)
        
        # Collect genre data for all artists in community
        for artist_id in community:
            for genre in id_to_genres.get(artist_id, []):
                genre_count[genre] = genre_count.get(genre, 0) + 1
        
        # Calculate genre prevalence as percentage
        genre_prevalence = {
            genre: (count/community_size * 100) 
            for genre, count in genre_count.items()
        }
        
        # Filter for significant genres (present in >30% of community)
        significant_genres = [
            genre for genre, prevalence 
            in genre_prevalence.items() 
            if prevalence >= 30
        ]
        
        # Get average popularity of community
        avg_popularity = sum(
            popularity_dict.get(artist_id, 0) 
            for artist_id in community
        ) / community_size
        
        # Sort artists by popularity
        sorted_artists = sorted(
            [
                {
                    'name': id_to_name.get(artist_id, 'Unknown'),
                    'id': artist_id,
                    'popularity': popularity_dict.get(artist_id, 0),
                    'genres': id_to_genres.get(artist_id, [])
                }
                for artist_id in community
            ],
            key=lambda x: x['popularity'],
            reverse=True
        )
        
        # Create community object
        community_data = {
            'community_id': community_id + 1,
            'size': community_size,
            'average_popularity': round(avg_popularity, 2),
            'main_genres': significant_genres,
            'genre_distribution': {
                genre: round(prev, 2) 
                for genre, prev in sorted(
                    genre_prevalence.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
            },
            'artists': sorted_artists
        }
        
        result.append(community_data)
    
    # Sort communities by size
    result.sort(key=lambda x: x['size'], reverse=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    return result



def save_recommendations_with_ids(recommendations, id_to_name, output_file):
    """Save recommendations with their artist IDs to a file."""
    # Reverse lookup: name to ID mapping
    name_to_id = {name: id for id, name in id_to_name.items()}
    
    # Add IDs to recommendations
    recommendations_with_ids = []
    for rec in recommendations:
        rec_with_id = rec.copy()
        artist_name = rec['artist']
        if artist_name in name_to_id:
            rec_with_id['artist_id'] = name_to_id[artist_name]
        recommendations_with_ids.append(rec_with_id)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(recommendations_with_ids, f, indent=4, ensure_ascii=False)
    
    return recommendations_with_ids

def main(bababooey):
    # Load favorite artists
    artists_I_like = []
    with open("artist_counts_{}.json".format(bababooey)) as f:
        artist_data = json.load(f)
        for artist in artist_data:
            artists_I_like.append(artist['artist_id'])

    # Process each genre
    genres = ['edm', 'filmi', 'hip-hop', 'jazz', 'pop']
    all_recommendations = {}
    
    for genre in genres:
        print(f"\nProcessing {genre}...")
        
        # Load genre data
        with open(f"../data/something/{genre}.json", "r") as f:
            artist_dict = json.load(f)
            
        # Create adjacency list
        adj_list, id_to_name, popularity_dict, id_to_genres = create_adjacency_list(
            artist_dict, subset=1000)
            
        # Create and layout graph
        G, communities, pos, node_sizes, node_colors = create_graph(
            adj_list, id_to_name, popularity_dict, artists_I_like)
            
        # Generate recommendations
        recommendations = predict_next_artists(
            'artist_counts_{}.json'.format(bababooey), f'communities_{genre}.json', 50)
        
        # Save recommendations with IDs
        recommendations_with_ids = save_recommendations_with_ids(
            recommendations, 
            id_to_name, 
            f"../results/final2/{bababooey}/{genre}_recommendations_with_ids.json"
        )
        
        all_recommendations[genre] = recommendations_with_ids
            
        # Create visualizations
        plt = visualize_graph(
            G, pos, communities, node_sizes, node_colors, 
            id_to_name, artists_I_like, recommendations)
            
        # Save plots
        plt.savefig(
            f"../results/final2/{bababooey}/{genre}_with_recommendations.png", 
            dpi=300, bbox_inches='tight')
        plt.close()
    
    # Save all recommendations to a single file
    with open("../results/final2/{}/all_recommendations_with_ids.json".format(bababooey), 'w', encoding='utf-8') as f:
        json.dump(all_recommendations, f, indent=4, ensure_ascii=False)
    

if __name__ == "__main__":
    print("17-18")
    main("17-18")
    print("17-19")
    main("17-19")
    print("17-20")
    main("17-20")
    print("17-21")
    main("17-21")
    print("17-22")
    main("17-22")
    print("17-23")
    main("17-23")
    print("17-24")
    main("17-24")