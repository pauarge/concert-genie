import time
import numpy as np
import pandas as pd


def get_albums_info(sp_albums):
    album_names = []
    album_uris = []
    for i in range(len(sp_albums['items'])):
        album_names.append(sp_albums['items'][i]['name'])
        album_uris.append(sp_albums['items'][i]['uri'])
    return album_names, album_uris

def albumSongs(sp, uri, name, spotify_albums):
    album = uri #assign album uri to a_name
    spotify_albums[album] = {} #Creates dictionary for that specific album
    #Create keys-values of empty lists inside nested dictionary for album
    spotify_albums[album]['album'] = [] #create empty list
    spotify_albums[album]['track_number'] = []
    spotify_albums[album]['id'] = []
    spotify_albums[album]['name'] = []
    spotify_albums[album]['uri'] = []
    tracks = sp.album_tracks(album) #pull data on album tracks
    for n in range(len(tracks['items'])): #for each song track
            spotify_albums[album]['album'].append(name) #append album name tracked via album_count
            spotify_albums[album]['track_number'].append(tracks['items'][n]['track_number'])
            spotify_albums[album]['id'].append(tracks['items'][n]['id'])
            spotify_albums[album]['name'].append(tracks['items'][n]['name'])
            spotify_albums[album]['uri'].append(tracks['items'][n]['uri'])
    return spotify_albums


def get_artist_info(sp, raw_artist):
    result = sp.search(raw_artist)  # search query
    # Extract Artist's uri
    artist_uri = [x['uri'] for x in result['tracks']['items'][0]['artists'] if x['name'].lower() == raw_artist.lower()][0]

    # Pull all of the artist's albums
    sp_albums = sp.artist_albums(artist_uri, album_type='album')
    album_names, album_uris = get_albums_info(sp_albums)

    spotify_albums = {}
    album_count = 0
    checked_albs = []
    for i, name in zip(album_uris, album_names):  # each album
        if name not in checked_albs:
            checked_albs.append(name)
            spotify_albums = albumSongs(sp, i, name, spotify_albums)
            album_count += 1  # Updates album count once all tracks have been addedb

    return spotify_albums

def audio_features(sp, album):
    #Add new key-values to store audio features
    album['popularity'] = []
    #create a track counter
    track_count = 0
    for track in album['uri']:
        #pull audio features per track
        features = sp.audio_features(track)
        pop = sp.track(track)
        album['popularity'].append(pop['popularity'])
        track_count+=1

def info_pd(sp, spotify_albums):
    sleep_min = 2
    sleep_max = 5
    start_time = time.time()
    request_count = 0


    for i in spotify_albums:
        audio_features(sp, spotify_albums[i])
        request_count+=1
        if request_count % 5 == 0:
            print(str(request_count) + " playlists completed")
            time.sleep(np.random.uniform(sleep_min, sleep_max))
    dic_df = {}
    dic_df['album'] = []
    dic_df['track_number'] = []
    dic_df['id'] = []
    dic_df['name'] = []
    dic_df['uri'] = []
    dic_df['popularity'] = []
    for album in spotify_albums:
        for feature in dic_df.keys():
            dic_df[feature].extend(spotify_albums[album][feature])

    artist_df = pd.DataFrame.from_dict(dic_df)
    artist_df['name'] = artist_df['name'].apply(lambda x: x.lower())
    return artist_df

def get_popularity_song_art(sp, song, artist):
    for it in sp.search(song)['tracks']['items']:
        if it['artists'][0]['name'].lower() == artist.lower():
            return it['popularity']
    return 0