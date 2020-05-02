[![Build Status](https://travis-ci.com/tooxo/Geiler-Musik-Bot.svg?branch=master)](https://travis-ci.com/tooxo/Geiler-Musik-Bot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![CodeFactor](https://www.codefactor.io/repository/github/tooxo/geiler-musik-bot/badge)](https://www.codefactor.io/repository/github/tooxo/geiler-musik-bot)
[![Coverage Status](https://coveralls.io/repos/github/tooxo/Geiler-Musik-Bot/badge.svg?branch=develop)](https://coveralls.io/github/tooxo/Geiler-Musik-Bot?branch=develop)
# Geiler-Musik-Bot - Discord Music Playing

## What services are supported?
```sh
Spotify:
  - Tracks
  - Playlists
  - Artist Pages
  - Albums
    
Spotify URLs and Spotify URIs are supported!

YouTube:
  - Direct Links
  - Playlists
  
YouTube.com aswell as youtu.be URLs are supported. 

+ Youtube Search by Term
```

## Invitation Link
It's found on the website for the bot: https://d.chulte.de

## Can i host it for myself?
Sure, its a docker-compose container. You can for example host it on amazon aws free services.

Installation:
```sh
git clone https://github.com/tooxo/Geiler-Musik-Bot
cd Geiler-Musik-Bot
```
Then you need to setup the environment Variables for the bot. This is simply done by editing the sysenv.txt.example and renaming it to sysenv.txt afterwards.

Here are all the tokens explained:
```sh
> BOT_TOKEN=<your discord bot token>
> SPOTIFY_ID=<spotify app id>
> SPOTIFY_SECRET=<spotify app secret>
> PORT=<port for the webserver to run, defaults to 80>

Optional:
> MONGODB_URI=<for stats>
> MONGODB_USER=<mongodb user>
> LASTFM_KEY=<key for lastfm api. only needed if you want album covers to be displayed>
```

## Usage

* Play music:

    `.play <song link/playlist link/song name>`
    
    Aliases: `.p`<br>
    Example: `.play new rules dua lipa`
    

* Play music directly after the song currently playing (skip the Queue):
    
    ```.playnext <song link/playlist link/song name>```
    
    Aliases: `.pn`<br>
    Example: `.pn nice for what drake`
    
* Play music and skip to it instantly:

    `.playskip <song link/playlist link/song name>`
    
    Aliases: `.ps`<br>
    Example: `.ps do i wanna know? arctic monkeys`
    
* Skip one / multiple song:

    `.skip <(optional parameter) number of songs to skip, defaults to 1>`
    
    Aliases: `.s, .next`<br>
    Example:  `.skip 10`, `.skip`

* Show the current Queue:

    `.queue`
    
    Aliases: `.q`
    
* Shuffle the Queue:

    `.shuffle`
    
* Clears the Queue:

    `.clear`
    
* Show Information about the current song playing:

    `.info`
    
* Pauses the song:

    `.pause`
    
* Resumes if paused:

    `.resume`

* Stop playback

    `.stop`
    
* Changes the Volume:

    `.volume <value between 0.0 and 2.0>`
    
    Example: `.volume 1.2`
    
    _Volume gets applied on song changes._
    
* Renames the Bot:

    `.rename <new name>`
    
* Change the Characters used for the Song Progress Bar

    `.chars <full> <empty>`<br>
    `.chars reset` (Resets the Chars to Default)
    
    Example: `.chars █ ░` (This are also the example chars)<br>
    _For some example chars visit: https://changaco.oy.lc/unicode-progress-bars/_ 

    
## Found a bug?
File an issue here at github.

## Want different services supported?
File an issue, and I might implement it.