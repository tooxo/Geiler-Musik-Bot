FROM python:3.7-alpine
RUN apk add dumb-init
COPY requirements.txt /
RUN apk update && apk add opus-dev ffmpeg && pip install --index-url=https://s.chulte.de/pip/ pynacl aiohttp pycares cchardet chardet && pip install --upgrade -r requirements.txt
ENTRYPOINT ["/usr/bin/dumb-init"]