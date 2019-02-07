from flask import Flask, redirect, url_for, session, request, render_template
from flask_oauthlib.client import OAuth, OAuthException
from config import SPOTIFY_APP_ID, SPOTIFY_APP_SECRET

app = Flask(__name__)
app.secret_key = 'development'
app.config['SPOTIFY'] = dict(
    consumer_key=SPOTIFY_APP_ID,
    consumer_secret=SPOTIFY_APP_SECRET,
    base_url='https://accounts.spotify.com',
    request_token_url=None,
    access_token_url='/api/token',
    authorize_url='https://accounts.spotify.com/authorize',
)
oauth = OAuth(app)

spotify = oauth.remote_app(
    'spotify',
    app_key='SPOTIFY',
    # Change the scope to match whatever it us you need
    # list of scopes can be found in the url below
    # https://developer.spotify.com/web-api/using-scopes/
    request_token_params={'scope': 'user-read-email,playlist-read-private'},
)


@app.route('/')
def index():
    if 'spotify_token' in session:
        return render_template(
            'index.html',
            spotify_outh_status="Yes",
            kkbox_outh_status="No",
        )
    return render_template(
        'index.html',
        spotify_outh_status="No",
        kkbox_outh_status="No",
    )


@app.route('/login', methods=['POST'])
def login():
    platform = request.form.get('platform')
    if platform == "spotify":
        callback = url_for('spotify_authorized', next=None, _external=True)
        return spotify.authorize(callback=callback)
    else:
        return "kkbox"


@app.route('/login/authorized')
def spotify_authorized():
    resp = spotify.authorized_response()
    if resp is None:
        print('You denied the request to sign in.')
        return redirect(url_for('index'))

    session['spotify_token'] = resp['access_token']
    me = spotify.get('https://api.spotify.com/v1/me')
    return redirect(url_for('index'))


@spotify.tokengetter
def get_spotify_oauth_token():
    return session.get('spotify_token')


if __name__ == '__main__':
    app.run(debug=True)