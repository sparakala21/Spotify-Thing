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
scope = 'user-library-read'

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

def get_artist_network(genre, sp):
    if not sp.auth_manager.validate_token(sp.auth_manager.cache_handler.get_cached_token()):
        return None
    
    artists = []
    results = sp.search(q=f'genre:{genre}', type='artist', limit=50)
    
    while len(artists) < 100 and results['artists']['items']:
        for item in results['artists']['items']:
            try:
                # Verify artist exists
                sp.artist(item['id'])
                
                if len(artists) >= 100:
                    break
                artist_data = {
                    'id': item['id'],
                    'name': item['name'],
                    'genres': item['genres'],
                    'popularity': item['popularity']
                }
                if genre.lower() in ' '.join(item['genres']).lower():
                    artists.append(artist_data)
            except Exception as e:
                print(f"Invalid artist {item['name']}: {str(e)}")
                continue
        
        if len(artists) < 100 and results['artists']['next']:
            results = sp.next(results['artists'])
        else:
            break
    
    artist_network = {}
    for artist in artists:
        try:
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
        except Exception as e:
            print(f"Error getting related artists for {artist['name']} {artist['id']}: {str(e)}")
            continue
    
    return artist_network

@app.route('/')
def home():
    try:
        if not sp_oauth.validate_token(cache_handler.get_cached_token()):
            auth_url = sp_oauth.get_authorize_url()
            return redirect(auth_url)
        return redirect(url_for('get_network', genre='EDM'))
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        return str(e), 500

@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('get_network', genre='EDM'))

@app.route('/network')
def get_network():
    try:
        cache_handler = FlaskSessionCacheHandler(session)
        sp = Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            cache_handler=cache_handler,
            show_dialog=True
        ))
        
        genre = request.args.get('genre', 'EDM')
        network = get_artist_network(genre, sp)
        if network is None:
            return redirect(url_for('home'))
        return jsonify(network)
    except Exception as e:
        print(f"Error in network route: {str(e)}")
        return str(e), 500
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(port=8888)

