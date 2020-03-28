###############################
# Build the FFmpeg-build image.
FROM python:3.7-slim-buster as build

ARG FFMPEG_VERSION=4.2.2

ARG PREFIX=/opt/ffmpeg/
ARG LD_LIBRARY_PATH=/lib
ARG MAKEFLAGS="-j4"

RUN echo "deb http://deb.debian.org/debian buster non-free" >> /etc/apt/sources.list

# FFmpeg build dependencies.
RUN apt-get update && apt-get install -y \
  build-essential \
  coreutils \
  gcc \
  libmp3lame-dev \
  libogg-dev \
  libvpx-dev \
  libvorbis-dev \
  libwebp-dev \
  libtheora-dev \
  libopus-dev \
  openssl \
  libssl-dev \
  libfdk-aac-dev \
  pkg-config \
  librtmp-dev \
  wget \
  yasm

# Get ffmpeg source.
RUN cd /tmp/ && \
  wget http://ffmpeg.org/releases/ffmpeg-${FFMPEG_VERSION}.tar.gz && \
  tar zxf ffmpeg-${FFMPEG_VERSION}.tar.gz && rm ffmpeg-${FFMPEG_VERSION}.tar.gz

# Compile ffmpeg
RUN cd /tmp/ffmpeg-${FFMPEG_VERSION} && \
  ./configure \
  --enable-version3 \
  --enable-gpl \
  --enable-shared \
  --enable-nonfree \
  --enable-small \
  --enable-libmp3lame \
  --enable-libvpx \
  --enable-libtheora \
  --enable-libvorbis \
  --enable-libopus \
  --enable-libfdk-aac \
  --enable-libwebp \
  --enable-librtmp \
  --enable-postproc \
  --enable-openssl \
  --disable-debug \
  --disable-doc \
  --disable-ffplay \
  --extra-cflags="-I${PREFIX}/include" \
  --extra-ldflags="-L${LD_LIBRARY_PATH}" \
  --extra-libs="-lpthread -lm" \
  --prefix="${PREFIX}" && \
  make && make install && make distclean

RUN cp /opt/ffmpeg/bin/* /usr/bin
RUN mv /opt/ffmpeg/lib/pkgconfig/* /opt/ffmpeg/lib/ && rm -R /opt/ffmpeg/lib/pkgconfig/
RUN cp /opt/ffmpeg/lib/* /lib/

ENV PKG_CONFIG_PATH=/lib

RUN pip wheel av

# Cleanup.
RUN rm -rf /tmp/*

##########################
# Build the release image.
FROM python:3.7-slim-buster
LABEL MAINTAINER = "Till Schulte"

RUN echo "deb http://deb.debian.org/debian buster non-free" >> /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
  libpcre3-dev \
  libmp3lame-dev \
  libogg-dev \
  libvpx-dev \
  libvorbis-dev \
  libwebp-dev \
  libwebpmux3 \
  libfdk-aac-dev \
  libtheora-dev \
  libopus-dev \
  rtmpdump \
  git-core \
  wget

COPY --from=build /opt/ffmpeg/bin/* /usr/bin/
COPY --from=build /opt/ffmpeg/lib/* /lib/
COPY --from=build /av*.whl /

COPY requirements.txt /requirements.txt

RUN pip install -r /requirements.txt
RUN pip install av*.whl
RUN rm /av*.whl
RUN wget https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh -O /wait.sh && chmod +x /wait.sh