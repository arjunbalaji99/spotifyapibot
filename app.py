import spotipy
from flask import Flask, redirect, request, session

app = Flask(__name__)
app.secret_key = 'heyjakeimadeonephonecall'

SPOTIPY_CLIENT_ID = '711140f3324e4e2bb2dcb71c98c897a1'
SPOTIPY_CLIENT_SECRET = '05189b38b7804c6999503b751983987c'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:5000/callback'
SPOTIPY_SCOPE = 'user-top-read'

sp_oauth = spotipy.oauth2.SpotifyOAuth(
    SPOTIPY_CLIENT_ID,
    SPOTIPY_CLIENT_SECRET,
    SPOTIPY_REDIRECT_URI,
    scope=SPOTIPY_SCOPE
)

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
    
    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    
    return redirect('/user_data')

@app.route('/user_data')
def user_data():
    access_token = session.get('access_token')

    if access_token is None:
        return redirect('/login')

    sp = spotipy.Spotify(auth=access_token)

    top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')

    return f"Top Artists: {[artist['name'] for artist in top_artists['items']]}"

if __name__ == '__main__':
    app.run(debug=True)
