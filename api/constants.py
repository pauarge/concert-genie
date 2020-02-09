REDIS_URL = "redis://:password@localhost:6379/0"
API_KEY = "ad30e075-cc83-41c3-8708-dfb5625a2330"
BASE_URL = "https://api.setlist.fm/rest/1.0"
SPOTIFY_CLIENT_ID = '1f9afb3cf4f444d3b3a2f9d3bf20a4dc'
SPOTIFY_CLIENT_SECRET = '12f145a677b54fe6b6b05c52dcbd433b'

API_BASE = 'https://accounts.spotify.com'

# Make sure you add this to Redirect URIs in the setting of the application dashboard
REDIRECT_URI = "http://127.0.0.1:5000/api_callback"

SCOPE = 'playlist-modify-private,playlist-modify-public,user-top-read'

# Set this to True for testing but you probaly want it set to False in production.
SHOW_DIALOG = True
