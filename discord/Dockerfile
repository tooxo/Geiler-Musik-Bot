FROM python:3.7-slim-buster
COPY requirements.txt /
RUN apt-get update -qq && apt-get --no-install-recommends install libopus-dev wget xz-utils -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && wget -q https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -O ffmpeg.tar.xz \
 && tar -xf ffmpeg.tar.xz \
 && cd ffmpeg-* \
 && mv ffmpeg /usr/bin/ \
 && mv ffprobe /usr/bin/ \
 && cd .. \
 && rm -R ffmpeg* \
 && pip install -r requirements.txt