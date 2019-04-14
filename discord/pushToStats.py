import json as JSON
import io
import time
import os
import asyncio
from threading import Thread
import sys
from pymongo import MongoClient

def push_to_file(responsetime):
    responsetime = responsetime * 100
    if not (os.path.exists(file)):
        ff = io.open(file, "w+")
        ff.write("[]")
        ff.close()
    fileio = io.open(file, 'r+')
    string = fileio.read()
    fileio.close()
    try:
        y = eval(string)
    except Exception as e:
        y = []
    current_time = time.time()
    json_obj = {}
    json_obj["x"] = int(current_time * 1000)
    json_obj["y"] = round(responsetime, 0) * 10
    y.append(JSON.dumps(json_obj))
    l = []
    for x in y:
        x = eval(x)
        if not x['x'] < current_time - 60480000:
            l.append(str(x))
    out = io.open(file, 'w')
    out.write(str(l))
    out.close()

def push_to_file_thread(responsetime):
    thread = Thread(target=push_to_file, args=(responsetime,))
    thread.start()

mongo_url = os.environ['MONGODB_URI']
client = MongoClient(mongo_url)
db = client.heroku_zntw59v7
collection = db.connectiontime
def push_to_mongo(resp):
    current_time = time.time()
    all = collection.find()
    for item in all:
        if item['x'] < current_time - 60480000:
            collection.delete_one({'_id': item['_id']})
    obj = {'x': int(time.time()) * 1000, 'y': resp * 10}
    collection.insert_one(obj)

mostcollection = db.mostcollection
def push_to_most_mongo(songname):
    songname = songname.replace('"', "")
    songname = songname.replace("'", "")
    song = mostcollection.find_one({"name": songname})
    if song is not None:
        mostcollection.update_one({'_id': song['_id']}, {'$inc': {'val': 1}})
    else:
        obj = {'name': songname, 'val': 1}
        mostcollection.insert_one(obj)

def push_to_most_mongo_thread(songname):
    tg = Thread(target=push_to_most_mongo, args=(songname, ))
    tg.start()

def push_to_mongo_thread(resp):
    tj = Thread(target=push_to_mongo, args=(resp, ))
    tj.start()
