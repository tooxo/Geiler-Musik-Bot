[![Build Status](https://travis-ci.com/tooxo/Geiler-Musik-Bot.svg?branch=master)](https://travis-ci.com/tooxo/Geiler-Musik-Bot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

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
Sure, its a docker-compose container. You can for example host it via heroku. Visit https://dockhero.io/ for help.
```sh
#Startup
docker-compose up
#Startup detached
docker-compose up -d
```
You also need to set this environment variables in the sysenv.txt.example file and rename it to sysenv.txt before starting the container the first time.
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
