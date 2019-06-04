FROM python:3
COPY . /
RUN pip install -r requirements.txt
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get install -y libopus-dev ffmpeg
