from youtube_dl import YoutubeDL
import time
import asyncio
import datetime
import mongo
import requests


class Youtube:
    def __init__(self):
        print("[Startup]: Initializing YouTube Module . . .")
        self.epoch = time.time()
        self.mongo = mongo.Mongo()

    def youtube_term_sync(self, term):
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
                for item in info_dict['formats']:
                    if 'audio only' in item['format']:
                        dictionary['stream'] = item['url']
                dictionary['duration'] = str(datetime.timedelta(seconds=info_dict['entries'][0]['duration']))
            re = requests.head(dictionary['stream'])
            if re.status_code == 302 or re.status_code == 200:
                return dictionary
            else:
                dictionary['error'] = True
                return dictionary

    async def youtube_term(self, term):
        loop = asyncio.get_event_loop()
        youtube = await loop.run_in_executor(None, self.youtube_term_sync, term)
        asyncio.run_coroutine_threadsafe(self.mongo.append_response_time(youtube['loadtime']), loop)
        return youtube

    @staticmethod
    def youtube_url_sync(url):
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
            for item in info_dict['formats']:
                if 'audio only' in item['format']:
                    dictionary['stream'] = item['url']
            dictionary['duration'] = info_dict['duration']
        dictionary['loadtime'] = time.time() - start
        dictionary['error'] = False
        return dictionary

    async def youtube_url(self, url):
        loop = asyncio.get_event_loop()
        youtube = await loop.run_in_executor(None, self.youtube_url_sync, url)
        asyncio.run_coroutine_threadsafe(self.mongo.append_response_time(youtube['loadtime']), loop)
        return youtube

    @staticmethod
    def youtube_playlist_sync(url):
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

    async def youtube_playlist(self, url):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.youtube_playlist_sync, url)
