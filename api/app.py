import io
import json
import pickle
import time

import networkx as nx
import requests
import spotipy
from flask import Flask, request, jsonify, abort, Response, redirect, session
from flask_cors import CORS
from flask_redis import FlaskRedis
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from spotipy.oauth2 import SpotifyClientCredentials

from constants import BASE_URL, API_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, REDIRECT_URI, SCOPE
from lyrics import get_lyrics
from playlists import song_list_to_df, get_playlist, visualize, get_artist_picture, get_statistics

app = Flask(__name__)
app.secret_key = "super_secret_key"
CORS(app)
redis_client = FlaskRedis(app)

client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)  # spotify object to access API


def generate_playlists(artist):
    cache = redis_client.get(artist)
    cache_stats = redis_client.get('{}-stats'.format(artist))
    cache_uris = redis_client.get('{}-uris'.format(artist))
    if cache and cache_stats and cache_uris:
        return json.loads(cache), json.loads(cache_stats), json.loads(cache_uris)

    info_complete, df_pairs = song_list_to_df(artist)
    stats = get_statistics(info_complete)
    G = nx.from_pandas_edgelist(df_pairs, 'song_org', 'next_song', ['weight'], create_using=nx.DiGraph())
    playlist, playlist_score, uris = get_playlist(sp, G, artist)

    plot = visualize(G, playlist + ["end"])
    redis_client.set(artist, json.dumps(playlist_score))
    redis_client.set('{}-stats'.format(artist), json.dumps(stats))
    redis_client.set('{}-uris'.format(artist), json.dumps(uris))
    redis_client.set('{}-plot'.format(artist), pickle.dumps(plot))
    return playlist_score, stats, uris


# Checks to see if token is valid and gets a new token if not
def get_token():
    raw_token_info = redis_client.get("token_info")
    if raw_token_info:
        token_info = pickle.loads(raw_token_info)
    else:
        token_info = None

    # Checking if the session already has a token stored
    if not token_info:
        return token_info, False

    # Checking if token has expired
    now = int(time.time())
    is_token_expired = token_info.get('expires_at') - now < 60

    # Refreshing token if it has expired
    if is_token_expired:
        # Don't reuse a SpotifyOAuth object because they store token info and you could leak
        # user tokens if you reuse a SpotifyOAuth object
        sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id=SPOTIFY_CLIENT_SECRET, client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI, scope=SCOPE)
        token_info = sp_oauth.refresh_access_token(token_info.get('refresh_token'))

    return token_info, True


@app.route('/')
def generate():
    artist = request.args.get('artist')
    if artist:
        artist = artist.lower()
        playlist, statistics, uris = generate_playlists(artist)
        return jsonify({
            'playlist': playlist[1:],
            'img': get_artist_picture(sp, artist),
            'stats': statistics,
            'uris': uris
        }
        )
    abort(404)


@app.route('/suggest')
def suggest():
    artist = request.args.get('artist')
    if artist:
        artist = artist.lower()
        redis_key = 'suggest-{}'.format(artist)
        cached = redis_client.get(redis_key)
        if cached:
            return jsonify(json.loads(cached))

        artist_url = "{}/search/artists/?sort=relevance&artistName={}".format(BASE_URL, artist)
        headers = {'x-api-key': API_KEY, 'Accept': 'application/json'}
        r = requests.get(artist_url, headers=headers)
        result = r.json()
        names = list(map(lambda x: x.get('name'), result.get('artist')))
        if len(names) > 10:
            names = names[:10]
        redis_client.set(redis_key, json.dumps(names))
        return jsonify(names)
    abort(404)


@app.route('/lyrics')
def lyrics():
    artist = request.args.get('artist')
    song = request.args.get('song')
    if artist and song:
        artist = artist.lower()
        song = song.lower()
        result = get_lyrics(redis_client, artist, song)
        return jsonify(result)
    abort(404)


@app.route('/plot.png')
def plot_png():
    artist = request.args.get('artist')
    if artist:
        artist = artist.lower()
        cache = redis_client.get('{}-plot'.format(artist))
        if cache:
            fig = pickle.loads(cache)
            output = io.BytesIO()
            FigureCanvas(fig).print_png(output)
            return Response(output.getvalue(), mimetype='image/png')
    abort(404)


# authorization-code-flow Step 1. Have your application request authorization;
# the user logs in and authorizes access
@app.route("/verify")
def verify():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens
    # if you reuse a SpotifyOAuth object
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET,
                                           redirect_uri=REDIRECT_URI, scope=SCOPE)
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


# authorization-code-flow Step 2.
# Have your application request refresh and access tokens;
# Spotify returns access and refresh tokens
@app.route("/api_callback")
def api_callback():
    # Don't reuse a SpotifyOAuth object because they store token info and you could leak user tokens if you
    # reuse a SpotifyOAuth object
    sp_oauth = spotipy.oauth2.SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET,
                                           redirect_uri=REDIRECT_URI, scope=SCOPE)
    session.clear()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)

    # Saving the access token along with all other token related info
    redis_client.set('token_info', pickle.dumps(token_info))
    return jsonify(token_info)


# authorization-code-flow Step 3.
# Use the access token to access the Spotify Web API;
# Spotify returns requested data
@app.route("/create-playlist")
def create_playlist():
    artist = request.args.get('artist')
    uris = request.args.get('uris')
    if artist and uris:
        splitted_uris = uris.split(',')
        token_info, authorized = get_token()
        if not authorized:
            abort(403)
        spo = spotipy.Spotify(auth=token_info.get('access_token'))
        me = spo.me()
        response = spo.user_playlist_create(me.get('display_name'), 'ICHack - {}'.format(artist))
        print(json.dumps(response))
        resp2 = spo.user_playlist_add_tracks(me.get('display_name'), response.get('uri'), splitted_uris)
        print(json.dumps(resp2))
        return jsonify(response.get('external_urls').get('spotify'))
    abort(404)
