import json
import re
import urllib.request

from bs4 import BeautifulSoup


def get_lyrics(redis_client, artist, song_title):
    artist = artist.lower().replace(' ', '')
    song_title = song_title.lower().replace(' ', '')
    redis_key = 'lyrics-{}-{}'.format(artist, song_title)

    cached = redis_client.get(redis_key)
    if cached:
        return json.loads(cached)

    # remove all except alphanumeric characters from artist and song_title
    artist = re.sub('[^A-Za-z0-9]+', "", artist)
    song_title = re.sub('[^A-Za-z0-9]+', "", song_title)
    if artist.startswith("the"):  # remove starting 'the' from artist e.g. the who -> who
        artist = artist[3:]
    url = "http://azlyrics.com/lyrics/" + artist + "/" + song_title + ".html"

    try:
        content = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(content, 'html.parser')
        lyrics = str(soup)
        # lyrics lies between up_partition and down_partition
        up_partition = '<!-- Usage of azlyrics.com content by any third-party lyrics provider is prohibited by our ' \
                       'licensing agreement. Sorry about that. --> '
        down_partition = '<!-- MxM banner -->'
        lyrics = lyrics.split(up_partition)[1]
        lyrics = lyrics.split(down_partition)[0]
        lyrics = lyrics.replace('<br>', '').replace('</br>', '').replace('</div>', '').strip()
        redis_client.set(redis_key, json.dumps(lyrics))
        return lyrics
    except Exception as e:
        return "Exception occurred \n" + str(e)
