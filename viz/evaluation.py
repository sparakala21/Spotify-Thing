import json
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List

def load_evaluation_results(times: List[str]) -> Dict[str, Dict[str, List[float]]]:
    """Load evaluation results for all time periods and organize by metric."""
    metrics = {
        'hit_rate': defaultdict(list),
        'discovery_rate': defaultdict(list)
    }
    
    for time_period in times[:-1]:  # Exclude last period as it's only used for future data
        try:
            with open(f"../results/final2/{time_period}/prediction_evaluation.json", 'r') as f:
                results = json.load(f)
                
            # Store metrics for each genre
            for genre, data in results.items():
                if genre != 'overall':
                    metrics['hit_rate'][genre].append(data['hit_rate'])
                    
            # Store overall metrics
            metrics['hit_rate']['overall'].append(results['overall']['hit_rate'])
                    
        except FileNotFoundError:
            print(f"Warning: Could not find evaluation results for {time_period}")
    
    return metrics

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

def plot_metrics_over_time(times: List[str], metrics: Dict[str, Dict[str, List[float]]]):
    """Create visualizations for hit rates and discovery rates over time."""
    # Set up the plot style
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 16))
    
    # Define colors for each genre
    colors = {
        'edm': '#1DB954',      # Spotify green
        'filmi': '#FF9900',    # Orange
        'hip-hop': '#1DA1F2',  # Twitter blue
        'jazz': '#800080',     # Purple
        'pop': '#FF69B4',      # Hot pink
        'overall': '#36454F'   # Charcoal
    }
    
    # X-axis labels
    x_labels = [f"20{period}" for period in times[:-1]]
    x = np.arange(len(x_labels))
    
    # Plot hit rates
    ax1.set_title('Hit Rate Over Time by Genre', fontsize=16, pad=20)
    for genre, hit_rates in metrics['hit_rate'].items():
        line_style = '--' if genre == 'overall' else '-'
        line_width = 3 if genre == 'overall' else 2
        ax1.plot(x, hit_rates, label=genre.upper(), 
                color=colors[genre], linestyle=line_style, 
                linewidth=line_width, marker='o')
    
    ax1.set_xlabel('Time Period', fontsize=12)
    ax1.set_ylabel('Hit Rate (%)', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(x_labels, rotation=45)
    ax1.grid(True, linestyle='--', alpha=0.7)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    

    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('../results/final2/metrics_over_time.png', 
                dpi=300, bbox_inches='tight')
    plt.close()

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


def find_new_missed_artists(recommendations_file: str, 
                          historical_listens_file: str,
                          future_listens_file: str) -> List[Dict]:
    """
    Find new artists that appeared in future listening data but weren't recommended.
    Only includes artists that weren't in historical listening data.
    """
    # Load data
    with open(recommendations_file) as f:
        recommendations = json.load(f)
        recommended_artists = {
            rec['artist_id'] 
            for genre_recs in recommendations.values() 
            for rec in genre_recs 
            if 'artist_id' in rec
        }
    
    with open(historical_listens_file) as f:
        historical = json.load(f)
        historical_artists = {artist['artist_id'] for artist in historical}
    
    with open(future_listens_file) as f:
        future = json.load(f)
        
    # Find only new missed artists
    new_missed_artists = []
    for artist in future:
        if (artist['artist_id'] not in recommended_artists and 
            artist['artist_id'] not in historical_artists):
            new_missed_artists.append({
                'artist': artist['artist'],
                'artist_id': artist['artist_id'],
                'appearances': artist['appearances']
            })
    
    # Sort by number of appearances
    new_missed_artists.sort(key=lambda x: x['appearances'], reverse=True)
    return new_missed_artists

def print_new_missed_artists(missed_artists: List[Dict], time_period: str) -> None:
    """Print only new missed artists."""
    print(f"\nNEW MISSED ARTISTS FOR {time_period}")
    print("=" * 50)
    print(f"Total New Missed Artists: {len(missed_artists)}")
    
    if missed_artists:
        print("\nNew Artists (sorted by listen count):")
        for artist in missed_artists:
            print(f"{artist['artist_id']}: {artist['appearances']} songs")

if __name__ == "__main__":
    # from collections import defaultdict
    
    # times = ['17-18', '17-19', '17-20', '17-21', '17-22', '17-23', '17-24']
    # metrics = load_evaluation_results(times)
    # plot_metrics_over_time(times, metrics)

    # print_evaluation(metrics)
        
    times = ['17-18', '17-19', '17-20', '17-21', '17-22', '17-23', '17-24']
    
    for i in range(len(times)-1):
        missed_artists = find_new_missed_artists(
            f"../results/final/{times[i]}/all_recommendations_with_ids.json",
            f"artist_counts_{times[i]}.json",
            f"artist_counts_{times[i+1]}.json"
        )
        
        # Print summary
        print_new_missed_artists(missed_artists, times[i])