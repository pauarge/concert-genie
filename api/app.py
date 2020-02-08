import io
import json
import pickle

import networkx as nx
import requests
from flask import Flask, request, jsonify, abort, Response
from flask_cors import CORS
from flask_redis import FlaskRedis
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from constants import BASE_URL, API_KEY
from lyrics import get_lyrics
from playlists import song_list_to_df, get_playlist, visualize

app = Flask(__name__)
CORS(app)
redis_client = FlaskRedis(app)


def generate_playlists(artist):
    cache = redis_client.get(artist)
    if cache:
        return json.loads(cache)

    info_complete, df_pairs = song_list_to_df(artist)
    G = nx.from_pandas_edgelist(df_pairs, 'song_org', 'next_song', ['weight'], create_using=nx.DiGraph())
    playlist = get_playlist(G)

    plot = visualize(G, playlist)
    redis_client.set(artist, json.dumps(playlist))
    redis_client.set('{}-plot'.format(artist), pickle.dumps(plot))
    return playlist


@app.route('/')
def generate():
    artist = request.args.get('artist')
    if artist:
        artist = artist.lower()
        return jsonify(generate_playlists(artist)[1:])
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
