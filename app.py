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
users = []
cur_term_length = None

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
        return render_template('signin.html', auth_url = auth_url)

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
    users.clear()

    return render_template('createnewgroup.html')

@app.route('/datagatheringpage', methods=['GET', 'POST'])
def datagatheringpage():
    global tracks_info
    global artists_info
    global users
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    if spotify.me()['display_name'] not in users:
        settermlength(request.form.get('term_length', None))
        tallytotals(cur_term_length)
        users.append(spotify.me()['display_name'])

    return redirect('/algorithminformation')

@app.route('/algorithminformation')
def algorithminformation():
    return render_template('algorithminformation.html')

@app.route('/datadisplay')
def datadisplay():    
    tracks_info = gettrackinfo()
    artists_info = getartistinfo()
    return render_template('datadisplay.html', totaltopartists = artists_info, totaltopsongs = tracks_info, term = converttermlength(cur_term_length))

def settermlength(termlength):
    global cur_term_length
    if termlength != None:
        cur_term_length = termlength

def tallytotals(termlength):
    global total_top_artists
    global total_top_songs
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    top_artists = spotify.current_user_top_artists(limit=50, offset=0, time_range=termlength)
    counter = 50
    for artist in top_artists['items']:
        artist_name = artist['name']
        artist_image = artist['images'][0]['url'] if artist['images'] else None
        if artist_name in total_top_artists:
            total_top_artists[artist_name]['users'] += 1
            count = total_top_artists[artist_name]['count']
            users = total_top_artists[artist_name]['users']
            total_top_artists[artist_name]['count'] = ((count / (users - 1)) + counter) * (users ** 2)
        else:
            total_top_artists[artist_name] = {'count': counter, 'users': 1, 'image': artist_image}
        counter -= 1
    
    top_songs = spotify.current_user_top_tracks(limit=50, offset=0, time_range=termlength)
    counter = 50
    for song in top_songs['items']:
        track_name = song['name']
        artist_name = song['artists'][0]['name'] if song['artists'] else None
        album_cover = song['album']['images'][0]['url'] if song['album']['images'] else None

        if track_name in total_top_songs:
            total_top_songs[track_name]['users'] += 1
            count = total_top_songs[track_name]['count']
            users = total_top_songs[track_name]['users']
            total_top_songs[track_name]['count'] = ((count / (users - 1)) + counter) * (users ** 2)
        else:
            total_top_songs[track_name] = {'count': counter, 'artist': artist_name, 'users': 1, 'album_cover': album_cover}
        counter -= 1


def getartistinfo():
    sorted_artists = sorted(total_top_artists.items(), key=lambda x: x[1]['count'], reverse=True)
    top_artists = dict(sorted_artists[:50])
    artists_info = []

    for artist_name, artist_data in top_artists.items():
        artist_info = {
            'name': artist_name,
            'image': artist_data['image'],
            'count': artist_data['count']
        }
        artists_info.append(artist_info)
    
    return artists_info

def gettrackinfo():
    sorted_tracks = sorted(total_top_songs.items(), key=lambda x: x[1]['count'], reverse=True)
    top_tracks = dict(sorted_tracks[:50])
    tracks_info = []

    for track_name, track_data in top_tracks.items():
        track_info = {
            'name': track_name,
            'artist': track_data['artist'],
            'album_cover': track_data['album_cover'],
            'count': track_data['count']
        }
        tracks_info.append(track_info)
    
    return tracks_info

def converttermlength(cur_term_length):
    if cur_term_length == "short-term": return "Last 4 Weeks"
    elif cur_term_length == "medium-term": return "Last 6 Months"
    else: return "All Time"


if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 8080).split(":")[-1])))

# if __name__ == '__main__':
#     app.run(threaded=True)