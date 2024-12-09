import json
from collections import defaultdict
from typing import List

def count_artist_appearances(input_paths: List[str], output_path: str) -> None:
    """
    Count artist appearances across multiple JSON files and merge the results.
    
    Args:
        input_paths: List of paths to input JSON files
        output_path: Path where the merged results will be saved
    """
    # Initialize counters and ID storage
    artist_counts = defaultdict(int)
    artist_ids = {}
    
    # Process each input file
    for input_path in input_paths:
        try:
            with open(input_path) as f:
                data = json.load(f)
            
            # Count appearances and store IDs from this file
            for track in data:
                artist = track['artist']
                artist_counts[artist] += 1
                # Store/update artist ID (latest one will be kept if different across files)
                artist_ids[artist] = track['artist_id']
                
        except FileNotFoundError:
            print(f"Warning: Could not find file {input_path}")
        except json.JSONDecodeError:
            print(f"Warning: Invalid JSON in file {input_path}")
        except KeyError as e:
            print(f"Warning: Missing required field {e} in file {input_path}")
    
    # Format results
    results = [
        {
            'artist': artist,
            'artist_id': artist_ids[artist],
            'appearances': artist_counts[artist]
        }
        for artist in artist_counts
    ]
    
    # Sort by appearances (descending) and then artist name
    results.sort(key=lambda x: (-x['appearances'], x['artist']))
    
    # Write merged results to output file
    try:
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Successfully wrote merged results to {output_path}")
    except IOError:
        print(f"Error: Could not write to output file {output_path}")

# Example usage
if __name__ == '__main__':
    input_files = [
        '../data/2017.json',
        '../data/2018.json',
        '../data/2019.json',
        '../data/2020.json',
        '../data/2021.json',
        '../data/2022.json',
        '../data/2023.json',
        '../data/2024.json'
    ]
    #count_artist_appearances(input_files, 'artist_counts_17-19.json')