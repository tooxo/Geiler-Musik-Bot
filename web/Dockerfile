FROM python:3.7-alpine
COPY requirements.txt /
RUN apk --no-cache add libev-dev
RUN pip install --extra-index-url="https://s.chulte.de/pip/" --upgrade -r requirements.txt
