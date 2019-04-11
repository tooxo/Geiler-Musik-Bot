from django.http import HttpResponse
from pymongo import MongoClient
import os

def index(request):
    return HttpResponse(open('index.html', 'r').read())

def resp(request):
    return HttpResponse(open('response.html', 'r').read())

def mostplayed(request):
    return HttpResponse(open('mostplayed.html', 'r').read())

def mostjs(request):
    return HttpResponse(open('http/mostplayed.js', 'r').read())

def main(request):
    return HttpResponse(open('http/main.js', 'r').read())

def chart(request):
    return HttpResponse(open('http/chart.js', 'r').read())

def jquery(request):
    return HttpResponse(open('http/jquery.js', 'r').read())

mongo_url = os.environ['MONGODB_URI']
client = MongoClient(mongo_url)
db = client.heroku_zntw59v7

def mongo_request_resp(request):
    collection = db.connectiontime
    alfl = collection.find()
    ls = []
    for item in alfl:
        i = dict()
        i['x'] = item['x']
        i['y'] = item['y']
        ls.append(i)
    return HttpResponse(str(ls))

def mongo_request_most(request):
    collection = db.mostcollection
    alfal = collection.find()
    ls = []
    for item in alfal:
        i = dict()
        i['name'] = item['name']
        i['value'] = item['val']
        ls.append(i)
    return HttpResponse(str(ls))
