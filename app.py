import spotipy
from flask import Flask, redirect, request, session
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

SPOTIPY_CLIENT_ID = '711140f3324e4e2bb2dcb71c98c897a1'
SPOTIPY_CLIENT_SECRET = '05189b38b7804c6999503b751983987c'
SPOTIPY_REDIRECT_URI = 'https://spotify-stats-compiler.onrender.com/callback'
SPOTIPY_SCOPE = 'user-top-read'

sp_oauth = spotipy.oauth2.SpotifyOAuth(
    SPOTIPY_CLIENT_ID,
    SPOTIPY_CLIENT_SECRET,
    SPOTIPY_REDIRECT_URI,
    scope=SPOTIPY_SCOPE
)

user_sessions = {}

@app.route('/')
def home():
    return 'Welcome to your app! <a href="/login"> Login with Spotify </a>'

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    token_info = sp_oauth.get_access_token(request.args['code'])
    
    # Use a session ID instead of relying on Flask's default session
    session_id = os.urandom(24).hex()
    user_sessions[session_id] = {
        'access_token': token_info['access_token'],
        'refresh_token': token_info['refresh_token'],
    }
    
    # Set the session ID as a cookie
    response = redirect('/user_data')
    response.set_cookie('session_id', session_id)
    
    return response

@app.route('/user_data')
def user_data():
    session_id = request.cookies.get('session_id')
    
    # Check if the session ID exists in the user_sessions dictionary
    if session_id not in user_sessions:
        return redirect('/login')

    access_token = user_sessions[session_id]['access_token']

    sp = spotipy.Spotify(auth=access_token)

    top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')

    return f"Top Artists: {[artist['name'] for artist in top_artists['items']]}"

if __name__ == '__main__':
    app.run(debug=True)
