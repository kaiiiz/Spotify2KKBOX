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
    spotify_outh_status = True if spotify.access_token else False
    kkbox_outh_status = True if kkbox_blueprint.session.access_token else False
    return render_template(
        'index.html',
        spotify_outh_status=spotify_outh_status,
        kkbox_outh_status=kkbox_outh_status,
    )


@app.route('/login', methods=['POST'])
def login():
    platform = request.form.get('platform')
    if platform == "spotify":
        return redirect(url_for("spotify.login"))
    else:
        return redirect(url_for("kkbox.login"))


@app.route('/get/spotify_playlist')
def get_spotify_playlist():
    url = 'https://api.spotify.com/v1/me/playlists'
    headers = {'Authorization': 'Bearer ' + spotify.access_token}
    playlist = requests.get(url, headers=headers)
    return jsonify(playlist=playlist.json())


if __name__ == '__main__':
    app.run(debug=True)