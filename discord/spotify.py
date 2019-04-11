import time
import json as JSON
import math
import asyncio
import async_timeout
import aiohttp
import base64
import urllib.parse
import os

client_id = os.environ['spotify_id']
client_secret = os.environ['spotify_secret']

async def requestPost(session, url, header=None, body=None):
    with async_timeout.timeout(3):
        async with session.post(url, headers=header, data=body) as response:
            return await response.text()

async def requestGet(session, url, header):
    with async_timeout.timeout(3):
        async with session.get(url, headers=header) as response:
            return await response.text()

def gatherSpotifyTrack(track_url):
    token = util.oauth2.SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    cache_token = token.get_access_token()
    spotify = spotipy.Spotify(cache_token)
    track = spotify.track(track_url)
    return track['album']['artists'][0]['name'] + " - " + track['name']

async def requestToken(loop=None):
    str = client_id + ":" + client_secret
    enc = base64.b64encode(str.encode())
    url = "https://accounts.spotify.com/api/token"
    session = aiohttp.ClientSession()
    header =  {
        'Authorization': 'Basic ' + enc.decode(),
        'Content-Type': "application/x-www-form-urlencoded"
    }
    payload = "grant_type=client_credentials&undefined="
    test = await requestPost(session, url, header, payload)
    js = JSON.loads(test)
    await session.close()
    return js['access_token']

async def requestPlaylist(playlist_url, token):
    session = aiohttp.ClientSession()
    url = "https://api.spotify.com/v1/playlists/" + playlist_url + "/tracks?limit=100&offset=0"
    header = {
        'Authorization': 'Bearer ' + token
    }
    result = await requestGet(session, url, header)
    js = JSON.loads(result)
    track_count = js['total']
    tracklist = []
    for track in js['items']:
        tracklist.append(track['track']['album']['artists'][0]['name'] + " - "  + track['track']['name'])
    await session.close()
    session2 = aiohttp.ClientSession()
    if track_count > 100:
        url = "https://api.spotify.com/v1/playlists/" + playlist_url + "/tracks?offset=100&limit=100"
        result2 = await requestGet(session2, url, header)
        js2 = JSON.loads(result2)
        o = 0
        for track3 in js2['items']:
            tracklist.append(track3['track']['album']['artists'][0]['name'] + " - "  + track3['track']['name'])
    tracklist_prod = []
    for track in tracklist:
        if track not in tracklist_prod:
            tracklist_prod.append(track)
    await session2.close()
    return tracklist_prod

async def playlist_fetch_spotify(playlist_url):
    playlist_id = playlist_url.split("playlist/")[1]
    playlist_id = playlist_id.split("?si")[0]
    woop = await requestToken()
    suup = await requestPlaylist(playlist_id, woop)
    return suup
