FROM python:3.7-slim-buster
RUN apt update && apt-get install dumb-init
COPY requirements.txt /
RUN apt-get --no-install-recommends install libopus-dev wget xz-utils -y \
 && wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz -O ffmpeg.tar.xz \
 && tar -xf ffmpeg.tar.xz \
 && cd ffmpeg-* \
 && mv ffmpeg /usr/bin/ \
 && cd .. \
 && rm -R ffmpeg* \
 && pip install -r requirements.txt
ENTRYPOINT ["/usr/bin/dumb-init"]