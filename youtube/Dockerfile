FROM python:3.7-alpine

COPY requirements.txt /requirements.txt

RUN apk add gcc make libev-dev libc-dev

RUN pip install --upgrade pip \
    && pip install -r requirements.txt