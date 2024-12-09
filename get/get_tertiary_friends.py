import os
import json
from flask import Flask, request, redirect, session, url_for, jsonify

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

client_id = 'd2cd8af11d5e4e2c9f4c5d7bbfb38304'
client_secret = '4ad8673d99ef4032b66e86802191cf4a'
redirect_uri = 'http://localhost:8888/callback'
scope = 'user-library-read user-follow-read'

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

def get_artist_network():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        return None
    
    # Get user's followed artists
    followed_artists = []
    results = sp.current_user_followed_artists()
    
    while results:
        for item in results['artists']['items']:
            artist_data = {
                'id': item['id'],
                'name': item['name'],
                'genres': item['genres'],
                'popularity': item['popularity']
            }
            followed_artists.append(artist_data)
            
        if results['artists']['next']:
            results = sp.next(results['artists'])
        else:
            results = None
    
    # Get related artists for each followed artist
    artist_network = {}
    for artist in followed_artists:
        related = sp.artist_related_artists(artist['id'])
        related_data = [{
            'id': rel['id'],
            'name': rel['name'],
            'genres': rel['genres'],
            'popularity': rel['popularity']
        } for rel in related['artists']]
        
        artist_network[artist['name']] = {
            'artist': artist,
            'related_artists': related_data
        }
    
    return artist_network

@app.route('/')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('get_network'))

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_network'))

@app.route('/network')
def get_network():
    network = get_artist_network()
    if network is None:
        return redirect(url_for('home'))
    return jsonify(network)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(port=8888)