# remember to export client id, secret and redirect to run in development mode

import os
from flask import Flask, session, request, redirect, render_template
from flask_session import Session
import spotipy

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

total_top_artists = {}
total_top_songs = {}

@app.route('/')
def index():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-top-read',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return render_template('index.html', name = spotify.me()['display_name'])


@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')

@app.route('/create_new_group')
def create_new_group():
    total_top_artists.clear()
    total_top_songs.clear()

    tallytotals()
    return redirect("/datadisplay")

@app.route('/join_existing_group')
def join_existing_group():
    tallytotals()
    return redirect("/datadisplay")

@app.route('/datadisplay')
def datadisplay():
    return render_template('datadisplay.html', totaltopartists = total_top_artists, totaltopsongs = total_top_songs)

def tallytotals():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    top_artists = spotify.current_user_top_artists(limit=50, offset=0, time_range="medium_term")
    counter = 50
    for artist in top_artists['items']:
        if artist['name'] in total_top_artists:
            total_top_artists[artist['name']] = total_top_artists[artist['name']] + counter
        else:
            total_top_artists[artist['name']] = counter
        counter = counter - 1
    
    top_songs = spotify.current_user_top_tracks(limit=50, offset=0, time_range="medium_term")
    counter = 50
    for songs in top_songs['items']:
        if songs['name'] in total_top_songs:
            total_top_songs[songs['name']] = total_top_songs[songs['name']] + counter
        else:
            total_top_songs[songs['name']] = counter
        counter = counter - 1


if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))

# if __name__ == '__main__':
#     app.run(threaded=True)