FROM python:3.7-slim-buster

COPY requirements.txt /requirements.txt

RUN apt-get update -qq && apt-get --no-install-recommends install libopus-dev wget xz-utils pkg-config gcc make \
 libev-dev libc-dev libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libswscale-dev libswresample-dev \
 libavfilter-dev git -y \
 && apt-get autoremove -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && wget -q https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz -O ffmpeg.tar.xz \
 && tar -xf ffmpeg.tar.xz \
 && cd ffmpeg-* \
 && mv ffmpeg /usr/bin/ \
 && mv ffprobe /usr/bin/ \
 && cd .. \
 && rm -R ffmpeg* \
 && wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -O /wait.sh && chmod +x /wait.sh \
 && pip install --upgrade pip \
 && pip install -r /requirements.txt
