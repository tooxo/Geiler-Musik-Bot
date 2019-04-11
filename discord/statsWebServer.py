import http.server
import socketserver
from threading import Thread
import os
import requests
import time
import subprocess

PORT = int(os.environ['PORT'])

def keep_alive_thread():
    while True:
        r = requests.get('https://discordbot-tooxo.herokuapp.com/')
        print("Keeping it alive: " + str(r.status_code))
        time.sleep(500)

def server():
    task = ['gunicorn', '--bind', '0.0.0.0:' + str(PORT), '--chdir', './stats', 'stats.wsgi:application']
    subprocess.Popen(task)

def server_thread():
    thread = Thread(target=server)
    thread.start()
    thread2 = Thread(target=keep_alive_thread)
    thread2.start()
