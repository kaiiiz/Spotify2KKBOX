# Spotify2KKBOX

A song shift tool from spotify to kkbox (using kbl)

⚠️ Disclaimer: This tool is produced by the reverse engineering, and is my own works, KKBOX and Spotify aren't related to this tool. Be careful, there is no endorsement of this tool. Use at your own risk. 

## Background

Because KKBOX doesn't provide any API to modify playlist. The only way to convert playlist is using the import/export playlist features in KKBOX app.

So I wrote the python script in order to create kbl file last year, package it with flask and deploy it to heroku recently.

## How to use?

See [How to use](https://github.com/kaiiiz/Spotify2KKBOX/wiki/How-to-use%3F)

## Principle

1. Get spotify playlist with its API
2. Search keyword in KKBOX API
3. Use crawler to search kbl's track id in track url (because kbl's track id isn't same as API's track id)
4. Package all informations to kbl file

## How to run in local?

Since the free heroku plan, the transform progress may be extremely slow. I suggest to clone the project and run it locally if you expect the greater performance.

### Install

```
git clone https://github.com/kaiiiz/Spotify2KKBOX.git
cd Spotify2KKBOX
pipenv install
pipenv shell
```

### Configuration

Go to [KKBOX for developer](https://developer.kkbox.com/#/app), create app and set `redirect_url` to `http://localhost:5000/login/kkbox/authorized`

Go to [Spotify for developer](https://developer.spotify.com/dashboard/), create app and set `redirect_url` to `http://localhost:5000/login/spotify/authorized`

The final thing to do, copy your `client_id` and `client_secret` to `config.py`

### Run server

Back to command line, run

```
flask run
```

Open `localhost:5000` and follow the [tutorial](https://github.com/kaiiiz/Spotify2KKBOX/wiki/How-to-use%3F)
