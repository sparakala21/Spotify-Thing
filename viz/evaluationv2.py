import json
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import pandas as pd
from datetime import datetime

def evaluate_predictions(recommendations_file: str, 
                        historical_listens_file: str,
                        future_listens_file: str) -> Dict:
    """
    Evaluate how well artist recommendations predicted future listening behavior.
    
    Args:
        recommendations_file: Path to file containing artist recommendations
        historical_listens_file: Path to file containing historical listening data
        future_listens_file: Path to file containing future listening data
    
    Returns:
        Dictionary containing evaluation metrics
    """
    # Load data
    with open(recommendations_file) as f:
        recommendations = json.load(f)
    
    with open(historical_listens_file) as f:
        historical = json.load(f)
        historical_artists = {artist['artist_id'] for artist in historical}
    
    with open(future_listens_file) as f:
        future = json.load(f)
        future_artists = {artist['artist_id'] for artist in future}
    
    # Calculate metrics per genre
    results = {}
    for genre, genre_recs in recommendations.items():
        # Get recommended artist IDs for this genre
        recommended_artists = {
            rec['artist_id'] 
            for rec in genre_recs 
            if 'artist_id' in rec
        }
        
        # Calculate hit rate (what percentage of recommendations were listened to)
        hits = recommended_artists & future_artists
        hit_rate = len(hits) / len(recommended_artists) if recommended_artists else 0
        
        # Calculate discovery rate (what percentage of hits were new artists)
        new_discoveries = hits - historical_artists
        discovery_rate = len(new_discoveries) / len(hits) if hits else 0
        
        # Get detailed info about hits
        hit_details = []
        for artist_id in hits:
            # Get recommendation details
            rec_details = next(r for r in genre_recs if r.get('artist_id') == artist_id)
            
            # Get future listen count
            future_listens = next(
                a['appearances'] 
                for a in future 
                if a['artist_id'] == artist_id
            )
            
            hit_details.append({
                'artist': rec_details['artist'],
                'artist_id': artist_id,
                'recommended_score': rec_details['score'],
                'future_listens': future_listens,
                'was_new_discovery': artist_id in new_discoveries
            })
        
        results[genre] = {
            'total_recommendations': len(recommended_artists),
            'hit_rate': round(hit_rate * 100, 2),
            'discovery_rate': round(discovery_rate * 100, 2),
            'total_hits': len(hits),
            'new_discoveries': len(new_discoveries),
            'hit_details': sorted(hit_details, key=lambda x: x['future_listens'], reverse=True)
        }
    
    # Calculate overall metrics
    all_recommendations = {
        rec['artist_id'] 
        for genre_recs in recommendations.values() 
        for rec in genre_recs 
        if 'artist_id' in rec
    }
    total_hits = all_recommendations & future_artists
    total_discoveries = total_hits - historical_artists
    
    results['overall'] = {
        'total_recommendations': len(all_recommendations),
        'hit_rate': round(len(total_hits) / len(all_recommendations) * 100, 2),
        'discovery_rate': round(len(total_discoveries) / len(total_hits) * 100, 2) if total_hits else 0,
        'total_hits': len(total_hits),
        'new_discoveries': len(total_discoveries)
    }
    
    return results

def print_evaluation(results: Dict) -> None:
    """Print evaluation results in a readable format."""
    print("\nPREDICTION EVALUATION RESULTS")
    print("=" * 50)
    
    # Print overall results
    overall = results['overall']
    print(f"\nOVERALL PERFORMANCE:")
    print(f"Total Recommendations: {overall['total_recommendations']}")
    print(f"Hit Rate: {overall['hit_rate']}%")
    print(f"Discovery Rate: {overall['discovery_rate']}%")
    print(f"Total Hits: {overall['total_hits']}")
    print(f"New Discoveries: {overall['new_discoveries']}")
    
    # Print genre-specific results
    for genre, metrics in results.items():
        if genre != 'overall':
            print(f"\n{genre.upper()} GENRE:")
            print(f"Hit Rate: {metrics['hit_rate']}%")
            print(f"Discovery Rate: {metrics['discovery_rate']}%")
            print("\nSuccessful Recommendations:")
            for hit in metrics['hit_details']:
                new_tag = "[NEW]" if hit['was_new_discovery'] else ""
                print(f"- {hit['artist']} {new_tag}")
                print(f"  Score: {hit['recommended_score']:.2f}, Future Listens: {hit['future_listens']}")

if __name__ == "__main__":
    times = ['17-18', '17-19', '17-20', '17-21', '17-22', '17-23', '17-24']
    for i in range(len(times)-1):
        results = evaluate_predictions(
            f"../results/final/{times[i]}/all_recommendations_with_ids.json",
            f"artist_counts_{times[i]}.json",  # historical listening data
            f"artist_counts_{times[i+1]}.json"    # future listening data
        )
        
        # Save detailed results
        with open(f"../results/final/{times[i]}/prediction_evaluation.json", 'w') as f:
            json.dump(results, f, indent=4)
        
    
        # Print human-readable summary
        print_evaluation(results)