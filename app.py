# import os
# from flask import Flask, session, request, redirect, Session
# import spotipy

# app = Flask(__name__)
# app.config['SECRET_KEY'] = os.urandom(64)
# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_FILE_DIR'] = './.flask_session/'
# Session(app)

# SPOTIPY_CLIENT_ID = '711140f3324e4e2bb2dcb71c98c897a1'
# SPOTIPY_CLIENT_SECRET = '05189b38b7804c6999503b751983987c'
# SPOTIPY_REDIRECT_URI = 'https://spotify-stats-compiler.onrender.com/callback'
# SPOTIPY_SCOPE = 'user-top-read'

# sp_oauth = spotipy.oauth2.SpotifyOAuth(
#     SPOTIPY_CLIENT_ID,
#     SPOTIPY_CLIENT_SECRET,
#     SPOTIPY_REDIRECT_URI,
#     scope=SPOTIPY_SCOPE
# )

# @app.route('/')
# def home():
#     cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
#     return 'Welcome to your app! <a href="/login"> Login with Spotify </a>'

# @app.route('/login')
# def login():
#     auth_url = sp_oauth.get_authorize_url()
#     return redirect(auth_url)

# @app.route('/callback')
# def callback():
#     token_info = sp_oauth.get_access_token(request.args['code'])
    
#     session['access_token'] = token_info['access_token']
#     session['refresh_token'] = token_info['refresh_token']
    
#     return redirect('/user_data')

# @app.route('/user_data')
# def user_data():
#     access_token = session.get('access_token')

#     if access_token is None:
#         return redirect('/login')

#     sp = spotipy.Spotify(auth=access_token)

#     top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')

#     return f"Top Artists: {[artist['name'] for artist in top_artists['items']]}"

# if __name__ == '__main__':
#     app.run(debug=True)


import os
from flask import Flask, session, request, redirect, Session
import spotipy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


@app.route('/')
def index():

    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # Step 3. Signed in, display data
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
           f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
           f'<a href="/playlists">my playlists</a> | ' \
           f'<a href="/currently_playing">currently playing</a> | ' \
        f'<a href="/current_user">me</a>' \



@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()


'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))