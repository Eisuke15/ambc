FROM ubuntu:20.04
RUN apt update
RUN apt install -y python3.9
RUN apt install -y tcpdump
RUN apt install -y iproute2
RUN apt install -y curl
RUN mkdir /code
WORKDIR /code
COPY . /code/