FROM python:3.7-alpine
RUN apk --no-cache add dumb-init
COPY requirements.txt /
RUN apk update && apk --no-cache add opus-dev ffmpeg git  && pip install --extra-index-url=https://s.chulte.de/pip/ -r requirements.txt
ENTRYPOINT ["/usr/bin/dumb-init"]