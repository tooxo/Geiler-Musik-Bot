# Geiler-Musik-Bot
A discord-bot for playing music in discord.

# What services are supported?
Spotify Titles, Playlists, Artists & Albums; Youtube Links & Playlists; Search by Term [All Songs are played via YouTube]

# Gimme the invite link
Its on the statistics site of the bot: https://f.chulte.de

# Getting Started
```sh
> .help for basic help
> .play <thing to play> to play smth.
> .queue for viewing the queue
> .shuffle to shuffle the coming up songs
> .info to view information about the current song
```
# Can i host it for myself?
Sure, its hosted using heroku. Its free, i wont provide tutorial, but Ill help if needed.
The buildpacks you'll need:
```sh
> heroku/python
> https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
> https://github.com/ampledata/heroku-opus.git
```
You also need to set this environment variables
```sh
> BOT_TOKEN=<your discord bot token>
> SPOTIFY_ID=<spotify app id>
> SPOTIFY_SECRET=<spotify app secret>
> DJANGO_SECRET=<a key from this site https://www.miniwebtool.com/django-secret-key-generator/>
> PORT=<port for the webserver (not needed on heroku)>

Optional:
> MONGODB_URI=<for stats>
> MONGODB_USER=<mongodb user>
```
