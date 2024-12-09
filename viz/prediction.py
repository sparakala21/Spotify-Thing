import json
from collections import defaultdict
import numpy as np
from typing import List, Dict

class MusicRecommender:
    def __init__(self, user_artists: List[Dict], artist_communities: List[Dict]):
        self.user_artists = {artist["artist"]: artist["appearances"] 
                           for artist in user_artists}
        self.process_communities(artist_communities)
        
    def process_communities(self, communities: List[Dict]) -> None:
        """Process artist communities into an adjacency list and genre mappings."""
        self.artist_to_community = {}
        self.artist_genres = {}
        self.related_artists = defaultdict(set)
        self.communities = {}
        
        for community in communities:
            community_id = community["community_id"]
            self.communities[community_id] = set()
            
            for artist in community["artists"]:
                name = artist["name"]
                self.communities[community_id].add(name)
                self.artist_genres[name] = set(artist["genres"])
                self.artist_to_community[name] = community_id
            
            # Create connections between all artists in the same community
            for artist1 in self.communities[community_id]:
                for artist2 in self.communities[community_id]:
                    if artist1 != artist2:
                        self.related_artists[artist1].add(artist2)

    def get_recommendations_by_community(self, n_per_community: int = 5) -> List[Dict]:
        """Generate artist recommendations for each community based on user's listening history."""
        community_scores = defaultdict(lambda: defaultdict(float))
        
        # Calculate scores for all related artists within each community
        for user_artist, appearances in self.user_artists.items():
            if user_artist in self.related_artists:
                weight = np.log1p(appearances)
                
                for related_artist in self.related_artists[user_artist]:
                    if related_artist not in self.user_artists:
                        community_id = self.artist_to_community.get(related_artist)
                        
                        # Calculate genre similarity
                        user_artist_genres = self.artist_genres.get(user_artist, set())
                        related_artist_genres = self.artist_genres.get(related_artist, set())
                        
                        if user_artist_genres and related_artist_genres:
                            genre_similarity = len(
                                user_artist_genres & 
                                related_artist_genres
                            ) / len(
                                user_artist_genres | 
                                related_artist_genres
                            )
                        else:
                            genre_similarity = 0
                        
                        community_scores[community_id][related_artist] += weight * (1 + genre_similarity)

        # Get top recommendations for each community
        recommendations = []
        for community_id, scores in community_scores.items():
            top_community_recs = sorted(
                scores.items(),
                key=lambda x: x[1],
                reverse=True
            )[:n_per_community]
            
            for artist, score in top_community_recs:
                recommendations.append({
                    "artist": artist,
                    "score": round(score, 3),
                    "genres": list(self.artist_genres.get(artist, set())),
                    "community_id": community_id
                })
        
        # Sort all recommendations by score while maintaining community grouping
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations

def predict_next_artists(user_data_file: str, 
                        community_data_file: str, 
                        n_per_community: int = 5) -> List[Dict]:
    """Load data and return artist recommendations grouped by community."""
    with open(user_data_file) as f:
        user_artists = json.load(f)
    with open(community_data_file) as f:
        artist_communities = json.load(f)
        
    recommender = MusicRecommender(user_artists, artist_communities)
    return recommender.get_recommendations_by_community(n_per_community)

if __name__ == "__main__":
    print(predict_next_artists("artist_counts.json", "communities.json"))