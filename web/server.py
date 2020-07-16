"""
Server
"""
import hashlib
import json
import os

import bjoern
from flask import Flask, Response, redirect, request
from pymongo import MongoClient

HOST = "0.0.0.0"
PORT = 80
APP = Flask(__name__)

MONGO_URL = os.environ.get("MONGODB_URI", "")
CLIENT = MongoClient(MONGO_URL)
DB = CLIENT.discordbot


@APP.route("/check_password", methods=["POST"])
def check_password() -> Response:
    """
    Check the password
    @return:
    """
    hashed = request.form["password"]
    if (
        hashed
        == hashlib.sha256(
            os.environ.get("RESTART_PASSWORD").encode()
        ).hexdigest()
    ):
        document = DB.secure.find_one({"type": "restart_code"})
        return Response(document["code"])
    return Response("wrong_pw")


@APP.route("/restart_token")
def restart_token() -> Response:
    """
    Provide the restart token page
    @return:
    """
    with open("sites/password_check.html") as opened_file:
        return Response(opened_file.read())


@APP.route("/")
def index() -> Response:
    """
    Provide Index
    @return:
    """
    with open("sites/index.html") as opened_file:
        return Response(opened_file.read())


@APP.route("/response")
def response() -> Response:
    """
    Provide Response
    @return:
    """
    with open("sites/response.html") as opened_file:
        return Response(opened_file.read())


@APP.route("/mostplayed")
def mostplayed() -> Response:
    """
    Provide Most Played
    @return:
    """
    with open("sites/mostplayed.html") as opened_file:
        return Response(opened_file.read())


@APP.route("/http/mostplayed.js")
def mostplayedjs() -> Response:
    """
    Provide Most Played JS
    @return:
    """
    with open("scripts/mostplayed.js") as opened_file:
        return Response(opened_file.read())


@APP.route("/http/main.js")
def mainjs() -> Response:
    """

    @return:
    """
    with open("scripts/main.js") as opened_file:
        return Response(opened_file.read())


@APP.route("/sha256.js")
def sha256js() -> Response:
    """

    @return:
    """
    with open("scripts/sha256.js") as opened_file:
        return Response(opened_file.read())


@APP.route("/sjcl.js")
def sjcljs() -> Response:
    """

    @return:
    """
    with open("scripts/sjcl.js") as opened_file:
        return Response(opened_file.read())


@APP.route("/http/chart.js")
def chartjs() -> Response:
    """

    @return:
    """
    return redirect(
        "https://github.com/chartjs/Chart.js/releases/download/v2.9.3/Chart.bundle.js",
        302,
    )


@APP.route("/http/jquery.js")
def jqueryjs() -> Response:
    """

    @return:
    """
    return redirect(
        "https://ajax.googleapis.com/ajax/libs/jquery/3.4.0/jquery.min.js", 302
    )


@APP.route("/http/mongo_most")
def mongo_most() -> Response:
    """

    @return:
    """
    limit = request.args.get("limit", 0)

    collection = DB.most_played_collection
    alfal = collection.find()
    _list = []
    for item in alfal:
        _list.append({"name": item["name"], "value": item["val"]})
    _list = sorted(_list, key=lambda i: i["value"], reverse=True)
    if limit:
        return Response(json.dumps(_list[: int(limit)]))
    return Response(json.dumps(_list))


@APP.route("/http/mongo_response")
def mongo_response() -> Response:
    """
    @return:
    """
    collection = DB.connectiontime
    alfl = collection.find()
    _list = []
    for item in alfl:
        _list.append({"x": item["x"], "y": item["y"]})
    return Response(str(_list))


if __name__ == "__main__":
    bjoern.listen(host=HOST, port=PORT, wsgi_app=APP)
    bjoern.run()
