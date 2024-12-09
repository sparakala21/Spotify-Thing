import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = '75c2e795c347429bafca7016d7ffc59f'
client_secret = '02e9c6cc7d31478e9619c43a38ef41bc'
redirect_uri = 'http://localhost:8888/callback'
scope = 'user-top-read'

cache_handler = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

sp = Spotify(auth_manager=sp_oauth)

def get_top_artists(time_range='short_term', limit=50):
    """
    Get a user's top artists from Spotify
    
    Parameters:
        time_range (str): The time range to calculate top artists for
                         Options: short_term (~4 weeks), medium_term (~6 months), long_term (years)
        limit (int): Number of artists to return (max 50)
    
    Returns:
        list: List of dictionaries containing artist information
    """
    # Set up authentication with necessary scopes
    
    # Get top artists

    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return None
    
    results = sp.current_user_top_artists(
        limit=limit,
        offset=0,
        time_range=time_range
    )
    
    # Extract relevant information for each artist
    top_artists = []
    for idx, item in enumerate(results['items']):
        artist_info = {
            'rank': idx + 1,
            'name': item['name'],
            'genres': item['genres'],
            'popularity': item['popularity'],
            'spotify_url': item['external_urls']['spotify']
        }
        top_artists.append(artist_info)
    
    return top_artists

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('artists'))

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('artists'))

@app.route('/artists')
def artists():
    all_artists = get_top_artists()
    if all_artists is None:
        return redirect(url_for('home'))
    return jsonify(all_artists)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(port=8888)