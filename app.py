import os, random, string, xmltodict, requests, time
from flask import Flask, redirect, url_for, session, request, render_template, jsonify, send_from_directory, Response
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


def get_trackdata_in_kk(name, artist, album):
    if checkauth('kkbox'):
        headers = {
            'Authorization': 'Bearer ' + kkbox_blueprint.session.access_token
        }
    else:
        print('Check auth failed')
        return None

    # 0. Prepare variables
    NAME = name.lower()
    ABLUM = album.lower()
    ARTIST = artist.lower()

    # 1. Search album
    url = 'https://api.kkbox.com/v1.1/search'
    q = ARTIST + ' ' + ABLUM
    params = {
        'q': q,
        'type': 'album',
        'limit': 1,
    }
    try:
        req_search = requests.get(url, params=params, headers=headers).json()
    except requests.exceptions.ConnectionError:
        print('Connection error')
        return None
    else:
        album_id = req_search.get('albums').get('data')[0].get('id')

    # 2. Search track in album
    url = 'https://api.kkbox.com/v1.1/albums/' + album_id + '/tracks'
    try:
        req_album = requests.get(url, headers=headers).json().get('data')
    except requests.exceptions.ConnectionError:
        print('Connection error')
        return None
    else:
        track_id = ''
        for track in req_album:
            search_name = track.get('name').lower()
            if NAME in search_name or search_name in NAME:
                track_id = track.get('id')
                break
        if track_id == '':
            track_id = get_trackdata_in_kk_blurred(NAME, ARTIST, ABLUM)
            if track_id == '':
                print('Nothing found')
                return None

    # 3. Get track data by track_id
    url = 'https://api.kkbox.com/v1.1/tracks/' + track_id
    try:
        req_trackdata = requests.get(url, headers=headers).json()
    except requests.exceptions.ConnectionError:
        print('Connection error')
        return None
    else:
        return req_trackdata


def get_trackdata_in_kk_blurred(name, artist, album):
    if checkauth('kkbox'):
        headers = {
            'Authorization': 'Bearer ' + kkbox_blueprint.session.access_token
        }
    else:
        print('Check auth failed')
        return ''

    # 0. Prepare variables
    NAME = name.split('(')[0].split('-')[0].strip()
    ARTIST = artist.split('(')[0].split('-')[0].strip()
    ALBUM = album.split('(')[0].split('-')[0].strip()

    print('--- Blurred search: ' + NAME + '%%%%' + ARTIST + '%%' + ALBUM)

    # 1. Search name + artist
    url = 'https://api.kkbox.com/v1.1/search'
    q = NAME + ' ' + ARTIST
    params = {
        'q': q,
        'type': 'track',
        'limit': 50,
    }
    try:
        req_search = requests.get(url, params=params, headers=headers).json()
    except requests.exceptions.ConnectionError:
        print('Connection error')
        return None

    # 2. Filter result
    search_rst = req_search.get('tracks').get('data')
    track_id = ''
    for track in search_rst:
        search_name = track.get('name').lower()
        search_album = track.get('album').get('name').lower()
        search_artist = track.get('album').get('artist').get('name').lower()
        if NAME in search_name or search_name in NAME:
            print('- ' + search_name + '%%%%' + search_artist + '%%' +
                  search_album)
            if ARTIST in search_artist or search_artist in ARTIST or ALBUM in search_album or search_album in ALBUM:
                return track.get('id')

    # 3. Search name
    url = 'https://api.kkbox.com/v1.1/search'
    q = NAME
    params = {
        'q': q,
        'type': 'track',
        'limit': 50,
    }
    try:
        req_search = requests.get(url, params=params, headers=headers).json()
    except requests.exceptions.ConnectionError:
        print('Connection error')
        return None

    # 4. Filter result
    search_rst = req_search.get('tracks').get('data')
    for track in search_rst:
        search_name = track.get('name').lower()
        search_album = track.get('album').get('name').lower()
        search_artist = track.get('album').get('artist').get('name').lower()
        print('- ' + search_name + '%%%%' + search_artist + '%%' +
              search_album)
        if ARTIST in search_artist or search_artist in ARTIST:
            return track.get('id')

    return ''


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


@app.route('/search/all_tracks', methods=['POST'])
def search_all_tracks():
    playlists = request.form.to_dict()
    sp_playlists = []
    for p_name, p_id in playlists.items():
        tracks = all_tracks_in(p_id)
        sp_playlists.append([p_name, tracks])
    return jsonify(sp_playlists=sp_playlists)


@app.route('/search/trackdata_in_kkbox', methods=['POST'])
def search_trackdata_in_kkbox():
    sp_data = request.json['data']
    track_name = sp_data['track']['name']
    track_album = sp_data['track']['album']['name']
    track_artist = sp_data['track']['artists'][0]['name']
    kk_data = get_trackdata_in_kk(track_name, track_artist, track_album)
    if kk_data:
        track_data = {'status': 'success', 'data': kk_data}
        return jsonify(track_data=track_data)
    else:
        track_data = {'status': 'failed', 'data': sp_data}
        return jsonify(track_data=track_data)


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