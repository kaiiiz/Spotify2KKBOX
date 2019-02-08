import os
from flask import Flask, redirect, url_for, session, request, render_template, jsonify
from flask_dance.contrib.spotify import make_spotify_blueprint, spotify
from kkbox_auth import make_kkbox_blueprint
from config import SPOTIFY_APP_ID, SPOTIFY_APP_SECRET, KKBOX_APP_ID, KKBOX_APP_SECRET
import requests

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Disable HTTPS
app = Flask(__name__)
app.secret_key = 'development'

spotify_blueprint = make_spotify_blueprint(
    client_id=SPOTIFY_APP_ID,
    client_secret=SPOTIFY_APP_SECRET,
    scope='user-read-email playlist-read-private',
)
kkbox_blueprint = make_kkbox_blueprint(
    client_id=KKBOX_APP_ID,
    client_secret=KKBOX_APP_SECRET,
    authorization_url_params={'grant_type': 'client_credentials'},
)
app.register_blueprint(spotify_blueprint, url_prefix="/login")
app.register_blueprint(kkbox_blueprint, url_prefix="/login")


@app.route('/')
def index():
    spotify_outh_status = True if checkauth('spotify') else False
    kkbox_outh_status = True if checkauth('kkbox') else False
    return render_template(
        'index.html',
        spotify_outh_status=spotify_outh_status,
        kkbox_outh_status=kkbox_outh_status,
    )


def checkauth(platform):
    if platform == 'spotify':
        token = spotify.access_token
        if token:
            url = 'https://api.spotify.com/v1/me'
            headers = {'Authorization': 'Bearer ' + token}
            req = requests.get(url, headers=headers).json()
            if req.get('error'):
                return False
            else:
                return True
        else:
            return False
    elif platform == 'kkbox':
        token = kkbox_blueprint.session.access_token
        if token:
            url = 'https://api.kkbox.com/v1.1/charts'
            headers = {'Authorization': 'Bearer ' + token, 'territory': 'TW'}
            req = requests.get(url, headers=headers).json()
            if req.get('error'):
                return False
            else:
                return True
        else:
            return False


@app.route('/login', methods=['POST'])
def login():
    platform = request.form.get('platform')
    if platform == "spotify":
        return redirect(url_for("spotify.login"))
    elif platform == "kkbox":
        return redirect(url_for("kkbox.login"))
    else:
        return redirect(url_for("index"))


@app.route('/get/spotify/playlist')
def get_spotify_playlist():
    url = 'https://api.spotify.com/v1/me/playlists'
    headers = {'Authorization': 'Bearer ' + spotify.access_token}
    playlist = requests.get(url, headers=headers).json()
    return jsonify(playlist=playlist)


@app.route('/get/spotify/playlist/track')
def get_spotify_playlist_track():
    playlist_id = request.args.get('playlist_id', '', type=str)
    url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'
    headers = {'Authorization': 'Bearer ' + spotify.access_token}
    tracks_raw = requests.get(url, headers=headers).json()
    tracks = tracks_raw.get('items')
    """
    Spotify limits 100 songs in each query.
    So if playlist contains more than 100 songs, it must be queried multiple times to get whole playlists.
    """
    while tracks_raw.get('next'):
        tracks_raw = requests.get(
            tracks_raw.get('next'), headers=headers).json()
        tracks_next = tracks_raw.get('items')
        tracks += tracks_next
    return jsonify(tracks=tracks)


if __name__ == '__main__':
    app.run(debug=True)