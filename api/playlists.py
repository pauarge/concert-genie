import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import requests

from constants import API_KEY, BASE_URL
from spotify_info import get_artist_info, info_pd

MIN_SETLIST_LEN = 5
NUM_OF_PAGES = 5


def get_setlist_songs(raw_artist):
    artist_url = "{}/search/artists/?sort=relevance&artistName={}".format(BASE_URL, raw_artist)
    headers = {'x-api-key': API_KEY, 'Accept': 'application/json'}
    r = requests.get(artist_url, headers=headers)
    artists = r.json().get('artist')
    artist = artists[0]

    responses = []
    for i in range(1, NUM_OF_PAGES + 1):
        playlist_url = "{}/artist/{}/setlists/?p={}".format(BASE_URL, artist.get('mbid'), i)
        r = requests.get(playlist_url, headers=headers)
        responses.append(r.json())

    responses_setlist = map(lambda x: x.get('setlist'), responses)
    flattened_setlists = [item for sublist in responses_setlist for item in sublist if 'tour' in item.keys()]
    cleaned_setlists = list(map(lambda x: {
        'eventDate': x.get('eventDate'),
        'songs': list(map(lambda z: z.get('name'),
                          [item for sublist in map(lambda y: y.get('song'), x.get('sets').get('set')) for item in
                           sublist])),
        'tour': x.get('tour').get('name'),
        'country': x.get('venue').get('city').get('country').get('code')
    }, flattened_setlists))
    cleaned_setlists = [x for x in cleaned_setlists if 'songs' in x.keys()]
    cleaned_setlists = [x for x in cleaned_setlists if len(x['songs']) > 5]
    only_songs = list(map(lambda x: ["begin"] + x.get('songs') + ["end"], cleaned_setlists))

    return cleaned_setlists, only_songs


def song_list_to_df(raw_artist):
    cleaned_list, songs = get_setlist_songs(raw_artist)
    pairs = []
    for concert in cleaned_list:
        setlist = concert['songs']
        setlist = ['begin'] + setlist + ['end']
        for i in range(len(setlist) - 1):
            pairs.append((setlist[i], setlist[i + 1], concert['tour'], concert['country'], concert['eventDate']))

    df_pairs = pd.DataFrame(pairs)

    df_pairs = df_pairs.rename(columns={0: 'song_org', 1: 'next_song', 2: 'tour', 3: 'country', 4: 'date'})
    the_tour = df_pairs.sort_values(by=['date']).iloc[0]['tour']
    df_pairs2 = df_pairs[df_pairs.tour == the_tour]

    length_concert = df_pairs.groupby('date').count().median()['song_org']
    b = df_pairs2.groupby('date').count()
    dates = b[(b.song_org < length_concert + 2) & (b.song_org > length_concert - 2)].index

    df_pairs2 = df_pairs2[df_pairs.date.isin(dates)].groupby(['song_org', 'next_song']).size().reset_index().rename(
        columns={0: 'weight'})

    return df_pairs, df_pairs2


def get_playlist(G, pd_artist, source='begin', target='end'):
    visited = []
    visited_score = []
    cur = source

    while cur != target:
        if len(pd_artist[pd_artist['name'] == cur.lower()]) == 0:

            visited_score.append((cur, 0))
        else:
            popularity = pd_artist[pd_artist['name'] == cur.lower()].groupby('name').mean()
            visited_score.append((cur, int(popularity.iloc[0]['popularity'])))

        visited.append(cur)
        weights = []
        neighs = []
        for n in G.neighbors(cur):
            if n not in visited:
                weights.append(np.exp(G.get_edge_data(cur, n).get('weight')))
                neighs.append(n)
        weights = np.asarray(weights) / sum(weights)
        if len(weights) == 0:
            cur = target
        else:
            cur = np.random.choice(neighs, 1, p=weights)[0]

    return visited, visited_score


def visualize(G, playlist_go):
    all_weights = []

    f, ax = plt.subplots(figsize=(20, 20))
    plt.tight_layout()
    pos = nx.circular_layout(G)
    pos_higher = {}
    for k, v in pos.items():
        pos_higher[k] = (v[0] * 1.1, v[1] * 1.1)

    nx.draw_networkx_nodes(G.nodes, pos=pos)
    nx.draw_networkx_labels(G, pos=pos_higher)
    colors = ['r', 'b', 'y']
    edges_1 = []
    for i in range(len(playlist_go) - 1):
        edges_1.append((playlist_go[i], playlist_go[i + 1]))

    for (node1, node2, data) in G.edges(data=True):
        all_weights.append(data['weight'])

    unique_weights = list(set(all_weights))

    # plot edges with weighted widths
    for weight in unique_weights:
        # Form a filtered list with just the weight you want to draw
        weighted_edges = [(node1, node2) for (node1, node2, edge_attr) in G.edges(data=True) if
                          edge_attr['weight'] == weight]
        width = weight * 0.1
        nx.draw_networkx_edges(G, pos, edgelist=weighted_edges, width=width, edge_color='k', ax=ax)

    # plot Playlist path
    for ctr, edges_l in enumerate([edges_1]):
        nx.draw_networkx_edges(G, pos=pos, edgelist=edges_l, edge_color=colors[ctr], style='dashed', ax=ax, width=4,
                               alpha=0.5)

    return f


def get_artist_picture(sp, artist_raw):
    result = sp.search(artist_raw)  # search query
    # Extract Artist's uri
    artist_uri = [x['uri'] for x in result['tracks']['items'][0]['artists'] if x['name'].lower() == artist_raw.lower()][
        0]
    return sp.artist(artist_uri)['images'][0]['url']


def get_artist_info_spotify(sp, name):
    spotify_albums = get_artist_info(sp, name)
    return info_pd(sp, spotify_albums)
