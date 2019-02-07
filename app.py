from flask import Flask, redirect, url_for, session, request, render_template
from flask_dance.contrib.spotify import make_spotify_blueprint, spotify
from config import SPOTIFY_APP_ID, SPOTIFY_APP_SECRET, KKBOX_APP_ID, KKBOX_APP_SECRET

app = Flask(__name__)
app.secret_key = 'development'

spotify_blueprint = make_spotify_blueprint(
    client_id=SPOTIFY_APP_ID,
    client_secret=SPOTIFY_APP_SECRET,
    scope='user-read-email playlist-read-private',
)
app.register_blueprint(spotify_blueprint, url_prefix="/login")


@app.route('/')
def index():
    if not spotify.access_token:
        return render_template(
            'index.html',
            spotify_outh_status="No",
            kkbox_outh_status="No",
        )
    return render_template(
        'index.html',
        spotify_outh_status="Yes",
        kkbox_outh_status="No",
    )


@app.route('/login', methods=['POST'])
def login():
    platform = request.form.get('platform')
    if platform == "spotify":
        return redirect(url_for("spotify.login"))
    else:
        return "aaa"


if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc')