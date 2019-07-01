# FROM python:alpine3.7
# RUN apk update
# RUN apk add make automake gcc g++ subversion python3-dev
# FROM ubuntu:18.04
FROM python:3.7-stretch
MAINTAINER Prabhakaran Sampath “prabhakaran@zealtechlab.co.in”
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0", "index:app.server"]
