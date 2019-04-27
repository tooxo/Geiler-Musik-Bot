import json as JSON
import time
import asyncio
import async_timeout
import aiohttp
import base64
import urllib.parse
import os

class Spotify():
    def __init__(self):
        print("[Startup]: Initializing Spotify Module . . .")
        self.session = aiohttp.ClientSession()
        self.token = ""
        self.client_id = os.environ['SPOTIFY_ID']
        self.client_secret = os.environ['SPOTIFY_SECRET']

    async def requestPost(self, url, header=None, body=None):
        with async_timeout.timeout(3):
            async with self.session.post(url, headers=header, data=body) as response:
                return await response.text()

    async def requestGet(self, url, header):
        with async_timeout.timeout(3):
            async with self.session.get(url, headers=header) as response:
                return await response.text()

    async def invalidateToken(self):
        if self.token is not "":
            for x in range(1,3000):
                try:
                    asyncio.sleep(x)
                except Exception as e:
                    break
            self.token = ""

    async def requestToken(self):
        if (self.token is ""):
            str = self.client_id + ":" + self.client_secret
            enc = base64.b64encode(str.encode())
            url = "https://accounts.spotify.com/api/token"
            header =  {
                'Authorization': 'Basic ' + enc.decode(),
                'Content-Type': "application/x-www-form-urlencoded"
            }
            payload = "grant_type=client_credentials&undefined="
            test = await self.requestPost(url, header, payload)
            asyncio.ensure_future(self.invalidateToken())
            return JSON.loads(test)['access_token']
        else:
            return self.token

    async def spotifyTrack(self, track_url):
        token = await self.requestToken()
        track_id = track_url.split("track/")[1]
        if "?" in track_id:
            track_id = track_id.split("?")[0]
        url = "https://api.spotify.com/v1/tracks/" + track_id
        header = {
            'Authorization': 'Bearer ' + token
        }
        result = await self.requestGet(url, header)
        result = JSON.loads(result)
        return result['artists'][0]['name'] + " - " + result['name']

    async def spotifyPlaylist(self, playlist_url):
        token = await self.requestToken()
        playlist_id = playlist_url.split("playlist/")[1]
        if "?" in playlist_id:
            playlist_id = playlist_id.split("?si")[0]
        url = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks?limit=100&offset=0"
        header = {
            'Authorization': 'Bearer ' + token
        }
        result = await self.requestGet(url, header)
        js = JSON.loads(result)
        track_count = js['total']
        tracklist = []
        for track in js['items']:
            tracklist.append(track['track']['album']['artists'][0]['name'] + " - "  + track['track']['name'])
        if track_count > 100:
            url2 = "https://api.spotify.com/v1/playlists/" + playlist_id + "/tracks?limit=100&offset=100"
            result2 = await self.requestGet(url2, {'Authorization': 'Bearer ' + token})
            js2 = JSON.loads(result2)
            o = 0
            for track3 in js2['items']:
                tracklist.append(track3['track']['album']['artists'][0]['name'] + " - "  + track3['track']['name'])
        tracklist_prod = []
        for track in tracklist:
            if track not in tracklist_prod:
                tracklist_prod.append(track)
        return tracklist_prod

    async def spotifyAlbum(self, albumUrl):
        token = await self.requestToken()
        albumId = albumUrl.split("album/")[1]
        if "?" in albumId:
            albumId = albumId.split("?")[0]
        url = "https://api.spotify.com/v1/albums/" + albumId + "/tracks?limit=50"
        header = {
            'Authorization': 'Bearer '+token
        }
        result = await self.requestGet(url, header)
        js = JSON.loads(result)
        tracklist = []
        for item in js['items']:
            artist = item['artists'][0]['name']
            song = item['name']
            tracklist.append(artist + " - " + song)
        return tracklist

    async def spotifyArtist(self, artistUrl):
        token = await self.requestToken()
        artistId = artistUrl.split("artist/")[1]
        if "?" in artistId:
            artistId = artistId.split("?")[0]
        url = "https://api.spotify.com/v1/artists/" + artistId + "/top-tracks?country=DE"
        header = {
            'Authorization': 'Bearer ' + token
        }
        result = await self.requestGet(url, header)
        js = JSON.loads(result)
        tracklist = []
        for item in js['tracks']:
            artist = item['artists'][0]['name']
            song = item['name']
            tracklist.append(artist + " - " + song)
        return tracklist
