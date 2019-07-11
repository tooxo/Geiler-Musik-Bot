FROM python:3.7-alpine
COPY requirements.txt /
RUN apk update && apk add --update opus-dev ffmpeg gcc linux-headers libc-dev libffi-dev g++ make py3-aiohttp py3-pynacl && pip install --upgrade -r requirements.txt && pip install ./dependencies/*