import json

import networkx as nx
import pandas as pd
import requests
from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from flask_redis import FlaskRedis

from lyrics import get_lyrics

app = Flask(__name__)
CORS(app)
redis_client = FlaskRedis(app)

REDIS_URL = "redis://:password@localhost:6379/0"

API_KEY = "ad30e075-cc83-41c3-8708-dfb5625a2330"

BASE_URL = "https://api.setlist.fm/rest/1.0"
MIN_SETLIST_LEN = 5
NUM_OF_PAGES = 2


def get_setlist_songs(req_artist):
    cached = redis_client.get(req_artist)

    if cached:
        return json.loads(cached)

    artist_url = "{}/search/artists/?sort=relevance&artistName={}".format(BASE_URL, req_artist)
    headers = {'x-api-key': API_KEY, 'Accept': 'application/json'}
    r = requests.get(artist_url, headers=headers)
    artists = r.json().get('artist')
    artist = artists[0]

    responses = []
    for i in range(1, NUM_OF_PAGES):
        playlist_url = "{}/artist/{}/setlists/?p={}".format(BASE_URL, artist.get('mbid'), i)
        r = requests.get(playlist_url, headers=headers)
        responses.append(r.json())

    responses_setlist = map(lambda x: x.get('setlist'), responses)
    flattened_setlists = [item for sublist in responses_setlist for item in sublist]
    cleaned_setlists = list(map(lambda x: {
        'eventDate': x.get('eventDate'),
        'songs': list(map(lambda z: z.get('name'),
                          [item for sublist in map(lambda y: y.get('song'), x.get('sets').get('set')) for item in
                           sublist])),
        'tour': x.get('tour').get('name'),
        'country': x.get('venue').get('city').get('country').get('code')
    }, flattened_setlists))
    only_songs = list(map(lambda x: ["begin"] + x.get('songs') + ["end"], cleaned_setlists))

    redis_client.set(req_artist, json.dumps(only_songs))
    return only_songs


def song_list_to_df(artist):
    songs = get_setlist_songs(artist)
    pairs = []
    for setlist in songs:
        for i in range(0, len(setlist) - 1):
            pairs.append((setlist[i], setlist[i + 1]))

    df_pairs = pd.DataFrame(pairs)

    df_pairs = df_pairs.rename(columns={0: 'song_org', 1: 'next_song'})
    df_pairs = df_pairs.groupby(['song_org', 'next_song']).size().reset_index().rename(columns={0: 'weight'})

    return df_pairs


@app.route('/')
def generate():
    artist = request.args.get('artist')
    if artist:
        df_pairs = song_list_to_df(artist)
        graph = nx.from_pandas_edgelist(df_pairs, 'song_org', 'next_song', ['weight'], create_using=nx.DiGraph())

        visited = []
        cur = 'begin'
        while cur != 'end':
            visited.append(cur)
            max_n = None
            for n in graph.neighbors(cur):
                w = graph.get_edge_data(cur, n).get('weight')
                if not max_n or (max_n[1] < w and n not in visited):
                    max_n = (n, w)
            cur = max_n[0]

        visited.pop(0)
        return jsonify(visited)

    abort(404)


@app.route('/suggest')
def suggest():
    artist = request.args.get('artist')
    if artist:
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
        result = get_lyrics(redis_client, artist, song)
        return jsonify(result)
    abort(404)
