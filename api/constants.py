import os

BASE_URL = "https://api.setlist.fm/rest/1.0"

API_BASE = 'https://accounts.spotify.com'
REDIRECT_URI = "http://127.0.0.1:5000/api_callback"
SCOPE = 'playlist-modify-private,playlist-modify-public,user-top-read'
SHOW_DIALOG = True

API_KEY = os.environ.get('SETLIST_API_KEY')
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET')
REDIS_URL = os.environ.get('REDIS_URL')
