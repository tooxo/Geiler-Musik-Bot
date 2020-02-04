FROM python:3.7-slim-buster

COPY requirements.txt /requirements.txt

RUN apt-get update && apt-get install gcc make libev-dev libc-dev -y

RUN pip install --upgrade pip \
    && pip install -r requirements.txt