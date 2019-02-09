import os, random, string, xmltodict, requests
from flask import Flask, redirect, url_for, session, request, render_template, jsonify, send_from_directory
from flask_dance.contrib.spotify import make_spotify_blueprint, spotify
from kkbox_auth import make_kkbox_blueprint
from config import SPOTIFY_APP_ID, SPOTIFY_APP_SECRET, KKBOX_APP_ID, KKBOX_APP_SECRET

# Flask config
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Disable HTTPS

# Create Flask Instance
app = Flask(__name__)
app.secret_key = 'development'

# OAuth blueprint
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


# Utility function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] == 'kbl'


def checkauth(platform):
    if platform == 'spotify':
        token = spotify.access_token
        if token:
            url = 'https://api.spotify.com/v1/me'
            headers = {'Authorization': 'Bearer ' + token}
            req = requests.get(url, headers=headers)
            if req.status_code == 200:
                return True
            else:
                return False
        else:
            return False
    elif platform == 'kkbox':
        token = kkbox_blueprint.session.access_token
        if token:
            url = 'https://api.kkbox.com/v1.1/charts'
            headers = {'Authorization': 'Bearer ' + token, 'territory': 'TW'}
            req = requests.get(url, headers=headers)
            if req.status_code == 200:
                return True
            else:
                return False
        else:
            return False


def all_tracks_in(playlist_id):
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
    return tracks


# Web page
@app.route('/')
def index():
    spotify_outh_status = True if checkauth('spotify') else False
    kkbox_outh_status = True if checkauth('kkbox') else False
    kbl_kkbox_ver = session[
        'kbl_kkbox_ver'] if 'kbl_kkbox_ver' in session else 'Unknown'
    kbl_package_ver = session[
        'kbl_package_ver'] if 'kbl_package_ver' in session else 'Unknown'
    kbl_package_descr = session[
        'kbl_package_descr'] if 'kbl_package_descr' in session else 'Unknown'
    kbl_package_packdate = session[
        'kbl_package_packdate'] if 'kbl_package_packdate' in session else 'Unknown'
    kbl_status = 'Success' if 'kbl_status' in session else 'Unknown'
    return render_template(
        'index.html',
        spotify_outh_status=spotify_outh_status,
        kkbox_outh_status=kkbox_outh_status,
        kbl_kkbox_ver=kbl_kkbox_ver,
        kbl_package_ver=kbl_package_ver,
        kbl_package_descr=kbl_package_descr,
        kbl_package_packdate=kbl_package_packdate,
        kbl_status=kbl_status,
    )


@app.route('/convert_playlist', methods=['POST'])
def convert_playlist():
    print(request.form)
    return jsonify(a=None)


@app.route('/upload_kbl', methods=['POST'])
def upload_kbl():
    kbl = {
        'kkbox_ver': None,
        'package_ver': None,
        'package_descr': None,
        'package_packdate': None,
    }
    file = request.files.get('file')
    if not file:
        kbl['status'] = "Upload failed! File doesn't exist"
    elif not allowed_file(file.filename):
        kbl['status'] = "Upload failed! Unsupport file format"
    else:
        xml = file.read().decode('utf-8')
        try:
            content = xmltodict.parse(xml)
            content = content.get('utf-8_data').get('kkbox_package')
        except xmltodict.expat.ExpatError:
            kbl['status'] = 'Upload failed! kbl file parse failed!'
            return jsonify(kbl=kbl)
        else:
            kkbox_ver = content.get('kkbox_ver')
            package_ver = content.get('package').get('ver')
            package_descr = content.get('package').get('descr')
            package_packdate = content.get('package').get('packdate')
            session['kbl_kkbox_ver'] = kkbox_ver or ''
            session['kbl_package_ver'] = package_ver or ''
            session['kbl_package_descr'] = package_descr or ''
            session['kbl_package_packdate'] = package_packdate or ''
            session['kbl_status'] = 'Success'
            kbl['kkbox_ver'] = kkbox_ver or ''
            kbl['package_ver'] = package_ver or ''
            kbl['package_descr'] = package_descr or ''
            kbl['package_packdate'] = package_packdate or ''
            kbl['status'] = 'Success'
    return jsonify(kbl=kbl)


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
    if not checkauth('spotify'):
        return jsonify(status='failed')
    url = 'https://api.spotify.com/v1/me/playlists'
    headers = {'Authorization': 'Bearer ' + spotify.access_token}
    playlist = requests.get(url, headers=headers).json()
    return jsonify(playlist=playlist)


@app.route('/get/spotify/playlist/track')
def get_spotify_playlist_track():
    playlist_id = request.args.get('playlist_id', '', type=str)
    tracks = all_tracks_in(playlist_id)
    return jsonify(tracks=tracks)


if __name__ == '__main__':
    app.run(debug=True)