from youtube_dl import YoutubeDL
import time
import asyncio
import datetime
import mongo
import requests


class Youtube():
    def __init__(self):
        print("[Startup]: Initializing YouTube Module . . .")
        self.epoch = time.time()
        self.mongo = mongo.Mongo()

    def youtubeTermSync(self, term):
        now = time.time()
        if ' - ' in term:
            term = term.replace(" - ", " ")
        if now - self.epoch < 1:
            time.sleep(1)
        youtube_dl_opts = {
            'format': 'bestaudio/best'
        }
        dictionary = dict()
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info("ytsearch:" + term, download=False)
            dictionary['link'] = info_dict['entries'][0]['webpage_url']
            dictionary['title'] = info_dict['entries'][0]['title']
            dictionary['stream'] = info_dict['entries'][0]['formats'][1]['url']
            dictionary['duration'] = str(datetime.timedelta(seconds=info_dict['entries'][0]['duration']))
        end = time.time() - now
        dictionary['loadtime'] = end
        dictionary['term'] = term
        dictionary['error'] = False
        self.epoch = time.time()
        re = requests.head(dictionary['stream'])
        if re.status_code == 302 or re.status_code == 200:
            return dictionary
        else:
            with YoutubeDL(youtube_dl_opts) as ydl:
                info_dict = ydl.extract_info("ytsearch:" + term, download=False)
                dictionary['link'] = info_dict['entries'][0]['webpage_url']
                dictionary['title'] = info_dict['entries'][0]['title']
                dictionary['stream'] = info_dict['entries'][0]['formats'][1]['url']
                dictionary['duration'] = str(datetime.timedelta(seconds=info_dict['entries'][0]['duration']))
            re = requests.head(dictionary['stream'])
            if re.status_code == 302 or re.status_code == 200:
                return dictionary
            else:
                dictionary['error'] = True
                return dictionary

    async def youtubeTerm(self, term):
        loop = asyncio.get_event_loop()
        youtube = await loop.run_in_executor(None, self.youtubeTermSync, term)
        asyncio.run_coroutine_threadsafe(self.mongo.appendResponsetime(youtube['loadtime']), loop)
        return youtube

    def youtubeUrlSync(self, url):
        start = time.time()
        ydl_opts = {
            'skip_download': True,
            'format': 'bestaudio/best'
        }
        dictionary = dict()
        with YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            dictionary['link'] = url
            dictionary['title'] = info_dict['title']
            dictionary['stream'] = info_dict['formats'][1]['url']
            dictionary['duration'] = info_dict['duration']
        dictionary['loadtime'] = time.time() - start
        dictionary['error'] = False
        return dictionary

    async def youtubeUrl(self, url):
        loop = asyncio.get_event_loop()
        youtube = await loop.run_in_executor(None, self.youtubeUrlSync, url)
        asyncio.run_coroutine_threadsafe(self.mongo.appendResponsetime(youtube['loadtime']), loop)
        return youtube

    def youtubePlaylistSync(self, url):
        youtube_dl_opts = {
            'ignoreerrors': True,
            'extract_flat': True
        }
        output = []
        with YoutubeDL(youtube_dl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)
            for video in info_dict['entries']:
                if not video:
                    continue
                dic = dict()
                dic['title'] = video['title']
                dic['link'] = 'https://youtube.com/watch?v=' + video['url']
                output.append(dic)
        return output

    async def youtubePlaylist(self, url):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.youtubePlaylistSync, url)
