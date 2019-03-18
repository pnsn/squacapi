FROM python:3.6-alpine
MAINTAINER pnsn@uw.edu

ENV PYTHONUNBUFFERED 1
COPY ./requirements/ /requirements/

RUN pip install -r /requirements/local.txt

RUN mkdir /app
WORKDIR /app
COPY ./app/ /app

RUN adduser -D user

USER user
