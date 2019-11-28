from flask import Flask, request, Response
import time
import json
import requests
import random
import expiringdict
import string
import multiprocessing
import bjoern


class Parent:
    def __init__(self):
        self.app = Flask(__name__)
        self.nodes = list()
        self.cache = expiringdict.ExpiringDict(10000, 14000)
        self.search_cache = dict()
        self.process = multiprocessing.Process(target=self.check_if_alive_daemon)

    def check_if_alive_daemon(self):
        while True:
            time.sleep(10)
            _nodes = list()
            for node in self.nodes:
                try:
                    with requests.get(
                        "http://" + node["ip"] + ":" + node["port"] + "/health_check"
                    ) as r:
                        try:
                            int(r.text)
                        except ValueError:
                            continue
                        finally:
                            _nodes.append(node)
                except (requests.HTTPError, requests.ConnectionError) as err:
                    continue
                time.sleep(1)
            self.nodes = _nodes

    @staticmethod
    def generate_key(length):
        s = ""
        for x in range(length):
            s += random.choice(string.ascii_letters)
        return s

    def add_routes(self):
        @self.app.route("/register_node", methods=["POST"])
        def register_node():
            js = json.loads(request.data.decode())
            if js not in self.nodes:
                self.nodes.append(js)
                print("[*] New Node Registered [*]")
                print(
                    "[*] NodeId:",
                    js["node_id"],
                    "|",
                    "IP:",
                    js["ip"],
                    "|",
                    "PORT:",
                    js["port"],
                    "[*]",
                )
                print("[*] Now", len(self.nodes), "Nodes [*]")
            else:
                print("[*] New Node Registered [*]")
                print("[*]", js["node_id"], "was already there.", "[*]")
            return Response("", 200)

        @self.app.route("/logout", methods=["POST"])
        def logout():
            _id = request.data.decode()
            _nodes = list()
            for node in self.nodes:
                if node["node_id"] == _id:
                    continue
                _nodes.append(node)
            self.nodes = _nodes
            return "True"

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

        @self.app.route("/am_i_still_here")
        def am_i_still_online():
            _id = request.args.get("id", "")
            for node in self.nodes:
                if node["node_id"] == _id:
                    return Response("YES")
            return Response("NO")

        @self.app.route("/research/youtube_search", methods=["POST"])
        def youtube_search():
            if request.data in self.search_cache:
                return Response(self.search_cache[request.data])
            node = random.choice(self.nodes)
            r = requests.post(
                "http://"
                + node["ip"]
                + ":"
                + node["port"]
                + "/research/youtube_search",
                data=request.data,
            )
            url = r.text
            return Response(url, r.status_code)

        @self.app.route("/research/youtube_video", methods=["POST"])
        def youtube_video():
            _id = request.data.decode()
            if _id == "":
                return Response("Invalid ID", 400)

            node = random.choice(self.nodes)
            if _id in self.cache:
                _node = self.cache[_id]
                if _node in self.nodes:
                    node = _node
            self.cache[_id] = node

            tx = requests.post(
                "http://" + node["ip"] + ":" + node["port"] + "/research/youtube_video",
                data=_id,
            )
            return Response(tx.text, tx.status_code)

        @self.app.route("/research/youtube_playlist", methods=["POST"])
        def youtube_playlist():
            _id = request.data.decode()
            if _id == "":
                return Response("Invalid ID", 400)

            node = random.choice(self.nodes)
            return requests.post(
                "http://"
                + node["ip"]
                + ":"
                + node["port"]
                + "/research/youtube_playlist",
                _id,
            ).text

    def start_up(self):
        self.add_routes()
        self.process.start()
        bjoern.run(self.app, "0.0.0.0", 8008)


if __name__ == "__main__":
    parent = Parent()
    parent.start_up()
