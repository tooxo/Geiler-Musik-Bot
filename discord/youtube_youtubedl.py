from youtube_dl import YoutubeDL
import time
import asyncio
import datetime
from pushToStats import *

epoch = time.time()

def youtube_search_by_term(term):
    now = time.time()
    if now - epoch < 1.5:
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
    push_to_mongo_thread(end)
    return dictionary

async def youtube_search_by_term_async(term):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, youtube_search_by_term, term)

def get_youtube_by_url(url):
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
    push_to_mongo_thread(time.time() - start)
    return dictionary

async def get_youtube_by_url_async(url):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, get_youtube_by_url, url)

def youtube_search_by_playlist(url):
    start = time.time()
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

async def youtube_playlist_async(url):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, youtube_search_by_playlist, url)
