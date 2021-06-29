FROM ubuntu:20.04
RUN apt update
RUN apt install -y python3.9
RUN mkdir /code
WORKDIR /code
COPY . /code/