from flask import Flask, redirect, url_for, session, request, render_template, jsonify, send_from_directory, after_this_request
from flask_dance.contrib.spotify import make_spotify_blueprint, spotify
from kkbox_auth import make_kkbox_blueprint
from config import SPOTIFY_APP_ID, SPOTIFY_APP_SECRET, KKBOX_APP_ID, KKBOX_APP_SECRET
from werkzeug import secure_filename
import os, random, string, time, json, io, logging
import xmltodict, dicttoxml
import requests
import bs4

# Flask config
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Disable HTTPS
KBL_FOLDER = os.path.dirname(os.path.abspath(__file__)) + '/kbl'

# Create Flask Instance
app = Flask(__name__)
app.secret_key = 'development'
app.config['KBL_FOLDER'] = KBL_FOLDER

# Logging config
handler = logging.FileHandler('app.log', encoding='UTF-8')
logging_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s'
)
handler.setFormatter(logging_format)
app.logger.addHandler(handler)

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


def checkauth_spotify():
    token = spotify.access_token
    if token:
        url = 'https://api.spotify.com/v1/me'
        headers = {'Authorization': 'Bearer ' + token}
        for _ in range(5):  # Retry 5 times if connection error
            try:
                req = requests.get(url, headers=headers)
            except requests.exceptions.ConnectionError as e:
                app.logger.error('%s', e)
                continue
            else:
                if req.status_code == 200:
                    return True
                else:
                    app.logger.error('Spotify request failed')
                    return False
    else:
        app.logger.error("Spotify token doesn't exist")
        return False


def checkauth_kkbox():
    token = kkbox_blueprint.session.access_token
    if token:
        url = 'https://api.kkbox.com/v1.1/charts'
        headers = {'Authorization': 'Bearer ' + token, 'territory': 'TW'}
        for _ in range(5):  # Retry 5 times if connection error
            try:
                req = requests.get(url, headers=headers)
            except requests.exceptions.ConnectionError as e:
                app.logger.error('%s', e)
                continue
            else:
                if req.status_code == 200:
                    return True
                else:
                    app.logger.error('KKBOX request failed')
                    return False
    else:
        app.logger.error("KKBOX token doesn't exist")
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


def search_trackdata_in_kk(name, artist, album):
    if checkauth_kkbox():
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
    except Exception as e:
        print('[search_trackdata_in_kk] failed: ' + str(e))
        return None
    else:
        search_rst = req_search.get('albums').get('data')
        if search_rst:
            album_id = search_rst[0].get('id')
        else:
            return None

    # 2. Search track in album
    url = 'https://api.kkbox.com/v1.1/albums/' + album_id + '/tracks'
    try:
        req_album = requests.get(url, headers=headers).json().get('data')
    except Exception as e:
        print('[search_trackdata_in_kk] failed: ' + str(e))
        return None
    else:
        track_id = ''
        for track in req_album:
            search_name = track.get('name').lower()
            if NAME in search_name or search_name in NAME:
                track_id = track.get('id')
                break
        if track_id == '':
            track_id = search_trackdata_in_kk_blurred(NAME, ARTIST, ABLUM)
            if track_id == '':
                # print('Nothing found')
                return None

    # 3. Get track data by track_id
    url = 'https://api.kkbox.com/v1.1/tracks/' + track_id
    try:
        req_trackdata = requests.get(url, headers=headers).json()
    except Exception as e:
        print('[search_trackdata_in_kk] failed: ' + str(e))
        return None
    else:
        return req_trackdata


def search_trackdata_in_kk_blurred(name, artist, album):
    if checkauth_kkbox():
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

    # print('--- Blurred search: ' + NAME + '%%%%' + ARTIST + '%%' + ALBUM)

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
    except Exception as e:
        print('[search_trackdata_in_kk_blurred] failed: ' + str(e))
        return None

    # 2. Filter result
    search_rst = req_search.get('tracks').get('data')
    track_id = ''
    for track in search_rst:
        search_name = track.get('name').lower()
        search_album = track.get('album').get('name').lower()
        search_artist = track.get('album').get('artist').get('name').lower()
        if NAME in search_name or search_name in NAME:
            # print('- ' + search_name + '%%%%' + search_artist + '%%' +
            #       search_album)
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
    except Exception as e:
        print('[search_trackdata_in_kk_blurred] failed: ' + str(e))
        return None

    # 4. Filter result
    search_rst = req_search.get('tracks').get('data')
    for track in search_rst:
        search_name = track.get('name').lower()
        search_album = track.get('album').get('name').lower()
        search_artist = track.get('album').get('artist').get('name').lower()
        # print('- ' + search_name + '%%%%' + search_artist + '%%' +
        #   search_album)
        if ARTIST in search_artist or search_artist in ARTIST:
            return track.get('id')

    return ''


def get_trackdata_in_kk(track_id):
    if checkauth_kkbox():
        headers = {
            'Authorization': 'Bearer ' + kkbox_blueprint.session.access_token
        }
    else:
        return None

    url = 'https://api.kkbox.com/v1.1/tracks/' + track_id
    try:
        req_trackdata = requests.get(url, headers=headers).json()
    except Exception as e:
        print('[get_trackdata_in_kk] failed: ' + str(e))
        return None
    else:
        return req_trackdata


def get_kbl_pathname(song_name_url):
    try:
        r = requests.get(song_name_url)
    except Exception as e:
        print('[get_kbl_pathname] failed: ' + str(e))
        return None
    soup = bs4.BeautifulSoup(r.text, features="html5lib")
    song_pathname = soup.find("meta", property="al:ios:url")
    if (song_pathname):
        id_len = len(song_pathname["content"])
        return song_pathname["content"][18:id_len]
    else:
        return None


def get_kbl_artistid(song_artist_url):
    try:
        r = requests.get(song_artist_url)
    except Exception as e:
        print('[get_kbl_artistid] failed: ' + str(e))
        return None
    soup = bs4.BeautifulSoup(r.text, features="html5lib")
    song_pathname = soup.find("meta", property="al:ios:url")
    if (song_pathname):
        id_len = len(song_pathname["content"])
        return song_pathname["content"][15:id_len]
    else:
        return None


def get_kbl_albumid(song_album_url):
    try:
        r = requests.get(song_album_url)
    except Exception as e:
        print('[get_kbl_albumid] failed: ' + str(e))
        return None
    soup = bs4.BeautifulSoup(r.text, features="html5lib")
    song_pathname = soup.find("meta", property="al:ios:url")
    if (song_pathname):
        id_len = len(song_pathname["content"])
        return song_pathname["content"][14:id_len]
    else:
        return None


def get_kbl_template(playlistcnt, songcnt):
    if not (session.get('kbl_kkbox_ver') and session.get('kbl_package_ver') and
            session.get('kbl_package_packdate') and playlistcnt and songcnt):
        return None
    template = {
        "utf-8_data": {
            "kkbox_package": {
                "kkbox_ver": session["kbl_kkbox_ver"],
                "playlist": {},
                "package": {
                    "ver": session["kbl_package_ver"],
                    "descr": session["kbl_package_descr"],
                    "packdate": session["kbl_package_packdate"],
                    "playlistcnt": playlistcnt,
                    "songcnt": songcnt
                }
            }
        }
    }
    template = json.dumps(template)
    obj = json.loads(template)
    xml = dicttoxml.dicttoxml(obj, root=False, attr_type=False).decode('utf-8')
    return xml


def get_kbl_playlist_template(playlist_id, playlist_name):
    template = {
        "playlist": {
            "playlist_id": playlist_id,
            "playlist_name": playlist_name,
            "playlist_descr": "",
            "playlist_data": {}
        }
    }
    template = json.dumps(template)
    obj = json.loads(template)
    xml = dicttoxml.dicttoxml(obj, root=False, attr_type=False).decode('utf-8')
    return xml


def get_kbl_songdata_template(song_pathname, song_artist_id, song_album_id,
                              song_song_idx):
    template = {
        "song_data": {
            "song_pathname": song_pathname,
            "song_artist_id": song_artist_id,
            "song_album_id": song_album_id,
            "song_song_idx": song_song_idx
        }
    }
    template = json.dumps(template)
    obj = json.loads(template)
    xml = dicttoxml.dicttoxml(obj, root=False, attr_type=False).decode('utf-8')
    return xml


# Web page
@app.route('/')
def index():
    spotify_outh_status = True if checkauth_spotify() else False
    kkbox_outh_status = True if checkauth_kkbox() else False
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


@app.route('/download/generate_kbl', methods=['GET', 'POST'])
def download_generate_kbl():
    playlists = request.json
    playlistcnt = 0
    songcnt = 0
    for p in playlists:
        playlistcnt += 1
        for track in p[1]:
            songcnt += 1

    # 1. use playlist_xml replace '<playlist></playlist>'
    playlist_xml = ''
    kbl_template = get_kbl_template(playlistcnt, songcnt)
    if not kbl_template:  # generate failed
        reply = {
            'status':
            'failed',
            'msg':
            'generate failed, please upload kbl file to update required information.'
        }
        return jsonify(reply=reply)
    # 2. generate playlist_xml
    for idx, p in enumerate(playlists):
        p_name = p[0]
        # 1. use playlist_data_xml replace '<playlist_data></playlist_data>'
        playlist_data_xml = ''
        playlist_template = get_kbl_playlist_template(idx + 1, p_name)
        # 2. generate playlist_data_xml
        for track in p[1]:
            song_data = get_kbl_songdata_template(
                track['song_pathname'], track['song_artist_id'],
                track['song_album_id'], track['song_song_idx'])
            playlist_data_xml += song_data
        playlist_data_xml = '<playlist_data>' + playlist_data_xml + '</playlist_data>'
        # 3. replace it
        playlist_template = playlist_template.replace(
            '<playlist_data></playlist_data>', playlist_data_xml)
        playlist_xml += playlist_template
    # 3. replace it
    kbl_template = kbl_template.replace('<playlist></playlist>', playlist_xml)
    # 4. save kbl file
    random_list = random.choices(
        string.ascii_uppercase + string.digits + string.ascii_lowercase, k=20)
    filename = 'tmp-' + ''.join(random_list) + '.kbl'
    filepath = os.path.join(app.config['KBL_FOLDER'], filename)
    with open(filepath, 'w') as f:
        f.write(kbl_template)
    reply = {'msg': 'success', 'name': filename}
    return jsonify(reply=reply)


@app.route('/download/<filename>')
def download_kbl(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['KBL_FOLDER'], filename)

    @after_this_request
    def remove_kbl(response):
        try:
            os.remove(filepath)
        except Exception as e:
            print(e)
        return response

    return send_from_directory(
        app.config['KBL_FOLDER'],
        filename,
        mimetype='text/html',
        as_attachment=True,
        attachment_filename='spotify2kkbox.kbl')


@app.route('/convert/crawler_search_id', methods=['POST'])
def convert_crawler_search_id():
    track_id = request.json['track_id']
    track_data = get_trackdata_in_kk(track_id)
    name_url = track_data['url']
    artist_url = track_data['album']['artist']['url']
    album_url = track_data['album']['url']
    kbl_data = {}
    kbl_data['song_pathname'] = get_kbl_pathname(name_url)
    kbl_data['song_artist_id'] = get_kbl_artistid(artist_url)
    kbl_data['song_album_id'] = get_kbl_albumid(album_url)
    kbl_data['song_song_idx'] = track_data['track_number']
    if not (kbl_data['song_pathname'] and kbl_data['song_artist_id']
            and kbl_data['song_album_id']):
        # print('song_pathname', kbl_data['song_pathname'], name_url)
        # print('song_artist_id', kbl_data['song_artist_id'], artist_url)
        # print('song_album_id', kbl_data['song_album_id'], album_url)
        # print(track_data['album'])
        kbl = {'status': 'failed', 'track_data': track_data}
        return jsonify(kbl=kbl)
    else:
        kbl = {
            'status': 'success',
            'kbl_data': kbl_data,
            'track_data': track_data
        }
        return jsonify(kbl=kbl)


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
    kk_data = search_trackdata_in_kk(track_name, track_artist, track_album)
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


@app.route('/get/spotify_playlists')
def get_spotify_playlist():
    if not checkauth_spotify():
        return jsonify(status='failed')
    url = 'https://api.spotify.com/v1/me/playlists'
    headers = {'Authorization': 'Bearer ' + spotify.access_token}
    playlist = requests.get(url, headers=headers).json()
    return jsonify(playlist=playlist)


@app.route('/get/spotify_playlist_tracks')
def get_spotify_playlist_track():
    playlist_id = request.args.get('playlist_id', '', type=str)
    tracks = all_tracks_in(playlist_id)
    return jsonify(tracks=tracks)


if __name__ == '__main__':
    app.run(debug=True)