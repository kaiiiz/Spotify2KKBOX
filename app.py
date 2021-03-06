from flask import Flask, redirect, url_for, session, request, render_template, jsonify, send_from_directory, after_this_request
from flask_dance.contrib.spotify import make_spotify_blueprint, spotify
from kkbox_auth import make_kkbox_blueprint
from config import SPOTIFY_APP_ID, SPOTIFY_APP_SECRET, KKBOX_APP_ID, KKBOX_APP_SECRET
from werkzeug import secure_filename
from requests.adapters import HTTPAdapter
import os, random, string, time, json, io, logging
import logging.handlers
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
handler = logging.handlers.RotatingFileHandler(
    'log/app.log', maxBytes=104857600, backupCount=20
)
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
        ses = requests.Session()
        ses.mount('http://', HTTPAdapter(max_retries=5))
        ses.mount('https://', HTTPAdapter(max_retries=5))
        try:
            req = ses.get(url, headers=headers)
        except Exception as e:
            app.logger.error('%s, retry' % e)
        else:
            if req.status_code == 200:
                return True
            else:
                app.logger.error('Spotify request failed')
                return False
        return False  # After retry 5 times, return false
    else:
        app.logger.error("Spotify token doesn't exist")
        return False


def checkauth_kkbox():
    token = kkbox_blueprint.session.access_token
    if token:
        url = 'https://api.kkbox.com/v1.1/charts'
        headers = {'Authorization': 'Bearer ' + token, 'territory': 'TW'}
        ses = requests.Session()
        ses.mount('http://', HTTPAdapter(max_retries=5))
        ses.mount('https://', HTTPAdapter(max_retries=5))
        try:
            req = ses.get(url, headers=headers)
        except Exception as e:
            app.logger.error('%s, retry' % e)
        else:
            if req.status_code == 200:
                return True
            else:
                app.logger.error('KKBOX request failed')
                return False
        return False  # After retry 5 times, return false
    else:
        app.logger.error("KKBOX token doesn't exist")
        return False


def all_tracks_in(playlist_id):
    if not checkauth_spotify():
        app.logger.error('Spotify check auth failed')
        response = {
            'status': 'failed',
            'msg': "Spotify check auth failed, please login spotify.",
            'data': None,
        }
        return response
    else:
        """
        Spotify limits 100 songs in each query.
        So if playlist contains more than 100 songs, it must be queried multiple times to get whole playlists.
        """
        url = 'https://api.spotify.com/v1/playlists/' + playlist_id + '/tracks'
        headers = {'Authorization': 'Bearer ' + spotify.access_token}
        tracks_raw = requests.get(url, headers=headers).json()
        tracks = tracks_raw.get('items')
        while tracks_raw.get('next'):
            tracks_raw = requests.get(
                tracks_raw.get('next'), headers=headers).json()
            tracks_next = tracks_raw.get('items')
            tracks += tracks_next
        response = {
            'status': 'success',
            'msg': "Get all tracks in spotify playlist",
            'data': tracks,
        }
        return response


def search_trackdata_in_kk(name, artist, album):
    if not checkauth_kkbox():
        app.logger.error('KKBOX check auth failed')
        response = {
            'status': 'failed',
            'msg': "KKBOX check auth failed, please login KKBOX.",
            'data': None,
        }
        return response
    else:
        headers = {
            'Authorization': 'Bearer ' + kkbox_blueprint.session.access_token
        }
        ses = requests.Session()
        ses.mount('http://', HTTPAdapter(max_retries=5))
        ses.mount('https://', HTTPAdapter(max_retries=5))

    # 0. Prepare variables (case insensitive)
    SP_NAME = name.split('(')[0].split('-')[0].strip().lower()
    SP_ALBUM = album.split('(')[0].split('-')[0].strip().lower()
    SP_ARTIST = artist.split('(')[0].split('-')[0].strip().lower()

    # 1. Search album_id
    album_id = ''
    url = 'https://api.kkbox.com/v1.1/search'
    q = SP_ARTIST + ' ' + SP_ALBUM
    params = {
        'q': q,
        'type': 'album',
        'limit': 1,
    }
    try:
        r = ses.get(url, params=params, headers=headers).json()
    except Exception as e:
        app.logger.error('%s, retry' % e)
    else:
        search_rst = r.get('albums').get('data')
        if search_rst:
            album_id = search_rst[0].get('id')
    finally:
        if album_id == '':
            app.logger.warning(
                f'({SP_NAME} - {SP_ARTIST} - {SP_ALBUM}) not found (precisely)'
            )
            response = {
                'status': 'failed',
                'msg': "Precisely search failed",
                'data': None,
            }
            return response

    # 2. Search track_id in album
    track_id = ''
    url = 'https://api.kkbox.com/v1.1/albums/' + album_id + '/tracks'
    try:
        r = ses.get(url, headers=headers).json().get('data')
    except Exception as e:
        app.logger.error('%s, retry' % e)
    else:
        for track in r:
            search_rst = track.get('name').lower()
            if SP_NAME in search_rst or search_rst in SP_NAME:
                track_id = track.get('id')
                break
    finally:
        if track_id == '':
            app.logger.warning(
                f'({SP_NAME} - {SP_ARTIST} - {SP_ALBUM}) not found (precisely)'
            )
            response = {
                'status': 'failed',
                'msg': "Precisely search failed",
                'data': None,
            }
            return response

    # 3. Get track data by track_id
    track_data = None
    url = 'https://api.kkbox.com/v1.1/tracks/' + track_id
    try:
        r = ses.get(url, headers=headers).json()
    except Exception as e:
        app.logger.error('%s' % e)
    else:
        track_data = r
        response = {
            'status': 'success',
            'msg': 'Get track data in KKBOX (precisely search)',
            'data': track_data,
        }
        return response


def search_trackdata_in_kk_blurred(name, artist, album):
    if not checkauth_kkbox():
        app.logger.error('KKBOX check auth failed')
        response = {
            'status': 'failed',
            'msg': "KKBOX check auth failed, please login KKBOX.",
            'data': None,
        }
        return response
    else:
        headers = {
            'Authorization': 'Bearer ' + kkbox_blueprint.session.access_token
        }
        ses = requests.Session()
        ses.mount('http://', HTTPAdapter(max_retries=5))
        ses.mount('https://', HTTPAdapter(max_retries=5))

    # 0. Prepare variables
    SP_NAME = name.split('(')[0].split('-')[0].strip().lower()
    SP_ARTIST = artist.split('(')[0].split('-')[0].strip().lower()
    SP_ALBUM = album.split('(')[0].split('-')[0].strip().lower()

    # 1. Search name + artist
    track_id = ''
    track_data = None
    url = 'https://api.kkbox.com/v1.1/search'
    q = SP_NAME + ' ' + SP_ARTIST
    params = {
        'q': q,
        'type': 'track',
        'limit': 50,
    }
    try:
        r = ses.get(url, params=params, headers=headers).json()
    except Exception as e:
        app.logger.error('%s' % e)
    else:
        search_rst = r.get('tracks').get('data')
        for track in search_rst:
            kk_name = track.get('name').lower()
            kk_album = track.get('album').get('name').lower()
            kk_artist = track.get('album').get('artist').get('name').lower()
            if SP_NAME in kk_name or kk_name in SP_NAME:
                if SP_ARTIST in kk_artist or kk_artist in SP_ARTIST or SP_ALBUM in kk_album or kk_album in SP_ALBUM:
                    track_id = track.get('id')
                    break
    finally:
        if track_id != '':
            url = 'https://api.kkbox.com/v1.1/tracks/' + track_id
            try:
                r = ses.get(url, headers=headers).json()
            except Exception as e:
                app.logger.error('%s' % e)
            else:
                track_data = r
                response = {
                    'status': 'success',
                    'msg': 'Get track data in KKBOX (blurred)',
                    'data': track_data,
                }
                return response

    # 2. Search name
    track_id = ''
    track_data = None
    url = 'https://api.kkbox.com/v1.1/search'
    q = SP_NAME
    params = {
        'q': q,
        'type': 'track',
        'limit': 50,
    }
    try:
        r = ses.get(url, params=params, headers=headers).json()
    except Exception as e:
        app.logger.error('%s' % e)
    else:
        search_rst = r.get('tracks').get('data')
        for track in search_rst:
            kk_artist = track.get('album').get('artist').get('name').lower()
            if SP_ARTIST in kk_artist or kk_artist in SP_ARTIST:
                track_id = track.get('id')
                break
    finally:
        if track_id != '':
            url = 'https://api.kkbox.com/v1.1/tracks/' + track_id
            try:
                r = ses.get(url, headers=headers).json()
            except Exception as e:
                app.logger.error('%s' % e)
            else:
                track_data = r
                response = {
                    'status': 'success',
                    'msg': 'Get track data in KKBOX (blurred)',
                    'data': track_data,
                }
                return response
        else:
            app.logger.warning(
                f'({SP_NAME} - {SP_ARTIST} - {SP_ALBUM}) not found (blurred)')
            response = {
                'status': 'failed',
                'msg': "Blurred search failed",
                'data': None,
            }
            return response


def get_kbl_pathname(song_name_url):
    ses = requests.Session()
    ses.mount('http://', HTTPAdapter(max_retries=5))
    ses.mount('https://', HTTPAdapter(max_retries=5))
    try:
        r = ses.get(song_name_url)
    except Exception as e:
        app.logger.error('%s' % e)
    else:
        soup = bs4.BeautifulSoup(r.text, features="html5lib")
        song_pathname = soup.find("meta", property="al:ios:url")
        if song_pathname:
            id_len = len(song_pathname["content"])
            return song_pathname["content"][18:id_len]
        else:
            return None
    return None


def get_kbl_artistid(song_artist_url):
    ses = requests.Session()
    ses.mount('http://', HTTPAdapter(max_retries=5))
    ses.mount('https://', HTTPAdapter(max_retries=5))
    try:
        r = requests.get(song_artist_url)
    except Exception as e:
        app.logger.error('%s' % e)
    else:
        soup = bs4.BeautifulSoup(r.text, features="html5lib")
        song_artist_id = soup.find("meta", property="al:ios:url")
        if song_artist_id:
            id_len = len(song_artist_id["content"])
            return song_artist_id["content"][15:id_len]
        else:
            return None
    return None


def get_kbl_albumid(song_album_url):
    ses = requests.Session()
    ses.mount('http://', HTTPAdapter(max_retries=5))
    ses.mount('https://', HTTPAdapter(max_retries=5))
    try:
        r = requests.get(song_album_url)
    except Exception as e:
        app.logger.error('%s' % e)
    else:
        soup = bs4.BeautifulSoup(r.text, features="html5lib")
        song_album_id = soup.find("meta", property="al:ios:url")
        if song_album_id:
            id_len = len(song_album_id["content"])
            return song_album_id["content"][14:id_len]
        else:
            return None
    return None


def gen_kbl_template(playlistcnt, songcnt):
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


def gen_kbl_playlist_template(playlist_id, playlist_name):
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


def gen_kbl_songdata_template(song_pathname, song_artist_id, song_album_id,
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
    kbl_status = 'success' if 'kbl_status' in session else 'Unknown'
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
    kbl_template = gen_kbl_template(playlistcnt, songcnt)
    if not kbl_template:  # generate failed
        app.logger.error('generate failed, need kbl attributes')
        response = {
            'status': 'failed',
            'msg': 'generate failed, need kbl attributes',
            'filename': None,
        }
        return jsonify(response=response)

    # 2. generate playlist_xml
    for idx, p in enumerate(playlists):
        p_name = p[0]

        # A. use playlist_data_xml replace '<playlist_data></playlist_data>'
        playlist_data_xml = ''
        playlist_template = gen_kbl_playlist_template(idx + 1, p_name)

        # B. generate playlist_data_xml
        for track in p[1]:
            song_data = gen_kbl_songdata_template(
                track['song_pathname'], track['song_artist_id'],
                track['song_album_id'], track['song_song_idx'])
            playlist_data_xml += song_data
        playlist_data_xml = '<playlist_data>' + playlist_data_xml + '</playlist_data>'

        # C. replace it
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

    # 5. return filename
    response = {
        'status': 'success',
        'msg': 'generate success',
        'filename': filename,
    }
    return jsonify(response=response)


@app.route('/download/<filename>')
def download_kbl(filename):
    filename = secure_filename(filename)
    filepath = os.path.join(app.config['KBL_FOLDER'], filename)

    @after_this_request
    def remove_kbl(response):
        try:
            os.remove(filepath)
        except Exception as e:
            app.log.error('%s' % e)
        return response

    return send_from_directory(
        app.config['KBL_FOLDER'],
        filename,
        mimetype='text/html',
        as_attachment=True,
        attachment_filename='spotify2kkbox.kbl')


@app.route('/search/all_tracks_in_sp', methods=['POST'])
def search_all_tracks_in_sp():
    playlists = request.form.to_dict()
    sp_playlists = []
    for p_name, p_id in playlists.items():
        playlist = all_tracks_in(p_id)
        if playlist['status'] == 'failed':
            app.logger.error('Get all tracks failed - %s' % playlist['msg'])
            response = {
                'status': 'failed',
                'msg': playlist['msg'],
                'data': None,
            }
            return jsonify(response=response)
        else:
            sp_playlists.append([p_name, playlist['data']])
    response = {
        'status': 'success',
        'msg': 'Search all tracks in spotify success',
        'data': sp_playlists,
    }
    return jsonify(response=response)


@app.route('/search/kbl_attribute', methods=['POST'])
def search_kbl_attribute():
    sp_data = request.json['sp_data']
    sp_name = sp_data['track']['name']
    sp_album = sp_data['track']['album']['name']
    sp_artist = sp_data['track']['artists'][0]['name']
    # 1. Search trackdata in kkbox
    resp = search_trackdata_in_kk(sp_name, sp_artist, sp_album)
    if resp['status'] == 'failed' and resp['msg'] == "Precisely search failed":
        resp = search_trackdata_in_kk_blurred(sp_name, sp_artist, sp_album)
    if resp['status'] == 'failed':
        response = {
            'status': 'failed',
            'msg': resp['msg'],
            'data': {
                'track_data': sp_data,
                'kbl_attr': None,
            },
        }
        return jsonify(response=response)
    kk_data = resp['data']
    # 2. Search kbl attribute
    name_url = kk_data['url']
    artist_url = kk_data['album']['artist']['url']
    album_url = kk_data['album']['url']
    kbl_attr = {}
    kbl_attr['song_pathname'] = get_kbl_pathname(name_url)
    kbl_attr['song_artist_id'] = get_kbl_artistid(artist_url)
    kbl_attr['song_album_id'] = get_kbl_albumid(album_url)
    kbl_attr['song_song_idx'] = kk_data['track_number']
    if not (kbl_attr['song_pathname'] and kbl_attr['song_artist_id']
            and kbl_attr['song_album_id']):
        app.logger.warning(
            f'({sp_name} - {sp_artist} - {sp_album}) not found (kbl attr)')
        response = {
            'status': 'failed',
            'msg': "kbl attribute doesn't exist",
            'data': {
                'track_data': sp_data,
                'kbl_attr': None,
            },
        }
        return jsonify(response=response)
    else:
        response = {
            'status': 'success',
            'msg': "search kbl attribute",
            'data': {
                'track_data': kk_data,
                'kbl_attr': kbl_attr,
            },
        }
        return jsonify(response=response)


@app.route('/upload_kbl', methods=['POST'])
def upload_kbl():
    response = {
        'status': None,
        'msg': None,
        'data': {
            'kkbox_ver': None,
            'package_ver': None,
            'package_descr': None,
            'package_packdate': None,
        }
    }
    file = request.files.get('files[]')
    if not file:
        app.logger.error("Upload failed! File doesn't exist")
        response['status'] = "failed"
        response['msg'] = "File doesn't exist"
    elif not allowed_file(file.filename):
        app.logger.error("Upload failed! Unsupport file format")
        response['status'] = "failed"
        response['msg'] = "Unsupport file format"
    else:
        xml = file.read().decode('utf-8')
        try:
            content = xmltodict.parse(xml)
            content = content.get('utf-8_data').get('kkbox_package')
        except xmltodict.expat.ExpatError:
            app.logger.error("Upload failed! kbl file parse failed!")
            response['status'] = "failed"
            response['msg'] = "kbl file parse failed!"
        else:
            kkbox_ver = content.get('kkbox_ver') or ''
            package_ver = content.get('package').get('ver') or ''
            package_descr = content.get('package').get('descr') or ''
            package_packdate = content.get('package').get('packdate') or ''
            update_ses = {
                'kbl_status': 'success',
                'kbl_kkbox_ver': kkbox_ver,
                'kbl_package_ver': package_ver,
                'kbl_package_descr': package_descr,
                'kbl_package_packdate': package_packdate,
            }
            session.update(update_ses)
            update_resp = {
                'status': "success",
                'msg': "Upload success!",
                'data': {
                    'kkbox_ver': kkbox_ver,
                    'package_ver': package_ver,
                    'package_descr': package_descr,
                    'package_packdate': package_packdate,
                }
            }
            response.update(update_resp)
    return jsonify(response=response)


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
def get_spotify_playlists():
    if not checkauth_spotify():
        app.logger.error('Spotify check auth failed')
        response = {
            'status': 'failed',
            'msg': "Spotify check auth failed, please login spotify.",
            'data': None,
        }
        return jsonify(response=response)
    else:
        url = 'https://api.spotify.com/v1/me/playlists'
        headers = {'Authorization': 'Bearer ' + spotify.access_token}
        response = {
            'status': 'success',
            'msg': "Get playlists success",
            'data': {
                'playlists': requests.get(url, headers=headers).json()
            }
        }
        return jsonify(response=response)


@app.route('/get/spotify_playlist_tracks')
def get_spotify_playlist_track():
    playlist_id = request.args.get('playlist_id', '', type=str)
    tracks = all_tracks_in(playlist_id)
    return jsonify(tracks=tracks)


if __name__ == '__main__':
    app.run(debug=True)