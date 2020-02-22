import numpy as np
import pandas as pd
import requests

from constants import API_KEY, BASE_URL
from spotify_info import get_artist_info, info_pd, get_popularity_song_art, get_uri_song_art

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


def get_playlist(sp, G, artist, source='begin', target='end'):
    visited = []
    visited_score = []
    cur = source
    uris = []

    while cur != target:
        visited_score.append((cur, get_popularity_song_art(sp, cur, artist)))
        uri = get_uri_song_art(sp, cur, artist)
        if uri:
            uris.append(uri)

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

    return visited, visited_score, uris


def get_artist_picture(sp, artist_raw):
    result = sp.search(artist_raw)  # search query
    # Extract Artist's uri
    artist_uri = [x['uri'] for x in result['tracks']['items'][0]['artists'] if x['name'].lower() == artist_raw.lower()][
        0]
    return sp.artist(artist_uri)['images'][0]['url']


def get_artist_info_spotify(sp, name):
    spotify_albums = get_artist_info(sp, name)
    return info_pd(sp, spotify_albums)


def get_statistics(info_complete):
    stats = {}
    first_song = info_complete[info_complete.song_org == 'begin'].groupby('next_song').count(). \
        sort_values(by=['song_org']).reset_index()
    most_played = info_complete[['song_org', 'next_song']].groupby('next_song').count(). \
        sort_values(by='song_org').reset_index()

    last_song = info_complete[info_complete.next_song == 'end'].groupby('song_org').count(). \
        sort_values(by=['next_song']).reset_index()
    stats['first_song'] = first_song.iloc[-1].next_song
    stats['top_three'] = list(most_played[most_played['next_song'] != 'end'].iloc[-3:]['next_song'].unique()[::-1])
    stats['most_played'] = most_played[most_played['next_song'] != 'end'].iloc[-1]['next_song']
    stats['last_song'] = last_song.iloc[-1].song_org

    return stats
