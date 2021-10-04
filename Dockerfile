FROM python:3

ENV PYTHONUNBUFFERED 1
RUN mkdir /src
WORKDIR /src

ADD             ./requirements.txt ./
RUN             python3 -m pip install -r requirements.txt