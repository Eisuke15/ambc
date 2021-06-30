FROM ubuntu:20.04
RUN apt update
RUN apt install -y python3.9
RUN apt install -y tcpdump
RUN mkdir /code
WORKDIR /code
COPY . /code/