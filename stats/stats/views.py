from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from pymongo import MongoClient
import os
import hashlib


mongo_url_local = 'mongodb://database:27017/'
client_local = MongoClient(mongo_url_local)
db_local = client_local.discordbot

mongo_url = os.environ['MONGODB_URI']
client = MongoClient(mongo_url)
db = client.heroku_zntw59v7


@csrf_exempt
def check_password(request):
    hashed = request.POST.get('password', '')
    if hashed == hashlib.sha256(os.environ.get('RESTART_PASSWORD').encode()).hexdigest():
        document = db_local.secure.find_one({'type': 'restart_code'})
        return HttpResponse(document['code'])
    else:
        return HttpResponse('wrong_pw')


def restart_token(request):
    return HttpResponse(open('password_check.html').read())


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


def sha256(request):
    return HttpResponse(open('http/sha256.js').read())


def sjcl(request):
    return HttpResponse(open('http/sjcl.js').read())


def chart(request):
    return HttpResponseRedirect("https://github.com/chartjs/Chart.js/releases/download/v2.8.0/Chart.bundle.js")


def jquery(request):
    return HttpResponseRedirect("https://ajax.googleapis.com/ajax/libs/jquery/3.4.0/jquery.min.js")


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
