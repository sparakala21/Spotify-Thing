import json

with open('artist_counts_17-24.json') as f:
    future = json.load(f)
    future = sorted(future, key=lambda d: d['appearances'], reverse=True)
    print(future)
