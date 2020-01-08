from flask import Flask, request, Response
import requests
import random
import expiringdict
import string
import bjoern
import time
import threading
import socket
import os
import json


class Node:
    def __init__(self, thread):
        self.name = ""
        self.thread = thread
        self.ip = ""
        self.port = 0

    def enter_config(self, json_ob: dict):
        self.name = json_ob.get("name", "")
        self.ip = json_ob.get("ip", "")
        self.port = json_ob.get("port", "")


class ThreadedSocketServer:
    def __init__(self):
        self.HOST = "0.0.0.0"
        self.PORT = 9988
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.HOST, self.PORT))
        self.default_length = 16
        self.nodes = {}
        self.api_key = os.environ.get("API_KEY", "API_KEY")

    @staticmethod
    def is_json_valid(j: str):
        try:
            json.loads(j)
            return True
        except json.JSONDecodeError:
            return False

    def create_still_alive_message(self, length: int = None):
        if not length:
            length = self.default_length
        s = ""
        for x in range(length):
            s += random.choice(string.ascii_lowercase)
        return s

    def handle_client_connection(self, client: socket.socket, ip: tuple, _id: str):
        # authentication
        proposed_api_key = client.recv(1024).decode()
        if proposed_api_key != self.api_key:
            client.close()
            print("Connection", _id, "was rejected. [WRONG API KEY]")
            del self.nodes[_id]
            return
        client.sendall(b"ACCEPTED")

        # receive configuration
        sent_configuration = client.recv(1024).decode()
        if not self.is_json_valid(sent_configuration):
            client.close()
            print("Connection", _id, "was rejected. [WRONG CONFIGURATION]")
            del self.nodes[_id]
            return

        # put configuration
        parsed_configuration = json.loads(sent_configuration)
        self.nodes[_id].enter_config(parsed_configuration)

        while True:
            sma = self.create_still_alive_message().encode()
            try:
                client.sendall(sma)
            except BrokenPipeError:
                del self.nodes[_id]
                break
            resp = client.recv(1024)
            if sma != resp:
                del self.nodes[_id]
                break
            time.sleep(5)
        client.close()

    def listen(self):
        self.sock.listen(10)
        while True:
            _client, ip = self.sock.accept()
            _client.settimeout(10)
            print("Incoming Connection! [", ip, "]")
            _id = self.create_still_alive_message(8)
            thread = threading.Thread(
                target=self.handle_client_connection, args=(_client, ip, _id)
            )
            self.nodes[_id] = Node(thread=thread)
            thread.start()


class Parent:
    def __init__(self):
        self.app = Flask(__name__)
        self.cache = expiringdict.ExpiringDict(10000, 14000)
        self.search_cache = dict()
        self.socket_server = ThreadedSocketServer()
        threading.Thread(target=self.socket_server.listen).start()

    @staticmethod
    def generate_key(length):
        s = ""
        for x in range(length):
            s += random.choice(string.ascii_letters)
        return s

    def add_routes(self):
        @self.app.route("/new_node")
        def new_node():
            key = self.generate_key(16)
            r = requests.get("https://api.ipify.org?format=json")
            ip = r.json()["ip"]
            return Response(
                "parent_host="
                + ip
                + "</br>"
                + "node_id="
                + key
                + "</br>"
                + "parent_port=8123</br>"
                + "port=(enter open port)"
            )

        @self.app.route("/research/youtube_search", methods=["POST"])
        def youtube_search():
            if request.data in self.search_cache:
                return Response(self.search_cache[request.data])
            node: Node = self.socket_server.nodes[
                random.choice(list(self.socket_server.nodes.keys()))
            ]
            print("DEBUG | RECV, YT_SEARCH:", request.data, ";", "=>", node.name)
            r = requests.post(
                "http://" + node.ip + ":" + str(node.port) + "/research/youtube_search",
                data=request.data,
            )
            url = r.text
            return Response(url, r.status_code)

        @self.app.route("/research/youtube_video", methods=["POST"])
        def youtube_video():
            _id = request.data.decode()
            if _id == "":
                return Response("Invalid ID", 400)

            node: Node = self.socket_server.nodes[
                random.choice(list(self.socket_server.nodes.keys()))
            ]
            print("DEBUG | RECV, YT_VIDEO:", request.data, ";", "=>", node.name)
            if _id in self.cache:
                _node = self.cache[_id]
                if _node in self.socket_server.nodes:
                    node = _node
            self.cache[_id] = node

            tx = requests.post(
                "http://" + node.ip + ":" + str(node.port) + "/research/youtube_video",
                data=_id,
            )
            return Response(tx.text, tx.status_code)

        @self.app.route("/research/youtube_playlist", methods=["POST"])
        def youtube_playlist():
            _id = request.data.decode()
            if _id == "":
                return Response("Invalid ID", 400)

            node: Node = self.socket_server.nodes[
                random.choice(list(self.socket_server.nodes.keys()))
            ]
            print("DEBUG | RECV, YT_PLAYLIST:", request.data, ";", "=>", node.name)
            return requests.post(
                "http://"
                + node.ip
                + ":"
                + str(node.port)
                + "/research/youtube_playlist",
                _id,
            ).text

    def start_up(self):
        self.add_routes()
        bjoern.run(self.app, "0.0.0.0", 8008)


if __name__ == "__main__":
    parent = Parent()
    parent.start_up()
