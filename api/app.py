import networkx as nx
import pandas as pd
import requests
from flask import Flask
from flask_redis import FlaskRedis
from flask import jsonify
import json

app = Flask(__name__)
redis_client = FlaskRedis(app)

REDIS_URL = "redis://:password@localhost:6379/0"

ARTIST = "mumford and sons"
API_KEY = "ad30e075-cc83-41c3-8708-dfb5625a2330"

BASE_URL = "https://api.setlist.fm/rest/1.0"
MIN_SETLIST_LEN = 5
NUM_OF_PAGES = 2


def get_setlist_songs():
    cached = redis_client.get(ARTIST)

    if cached:
        return json.loads(cached)

    artist_url = "{}/search/artists/?sort=relevance&artistName={}".format(BASE_URL, ARTIST)
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

    redis_client.set(ARTIST, json.dumps(only_songs))
    return only_songs


def song_list_to_df():
    songs = get_setlist_songs()
    pairs = []
    for setlist in songs:
        for i in range(0, len(setlist) - 1):
            pairs.append((setlist[i], setlist[i + 1]))

    df_pairs = pd.DataFrame(pairs)

    df_pairs = df_pairs.rename(columns={0: 'song_org', 1: 'next_song'})
    df_pairs = df_pairs.groupby(['song_org', 'next_song']).size().reset_index().rename(columns={0: 'weight'})

    return df_pairs


@app.route('/')
def hello_world():
    df_pairs = song_list_to_df()
    G = nx.from_pandas_edgelist(df_pairs, 'song_org', 'next_song', ['weight'], create_using=nx.DiGraph())

    visited = []
    cur = 'begin'
    while cur != 'end':
        visited.append(cur)
        max_n = None
        for n in G.neighbors(cur):
            w = G.get_edge_data(cur, n).get('weight')
            if not max_n or (max_n[1] < w and n not in visited):
                max_n = (n, w)
        cur = max_n[0]

    visited.pop(0)
    return jsonify(visited)
