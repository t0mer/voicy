FROM ubuntu:18.04
LABEL maintainer="tomer.klein@gmail.com"

ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8

RUN apt update -yqq

RUN apt -yqq install python3-pip && \
    apt -yqq install libffi-dev && \
    apt -yqq install libssl-dev && \
    apt -yqq install portaudio19-dev && \
    apt -yqq install ffmpeg
    
RUN  pip3 install --upgrade pip --no-cache-dir && \
     pip3 install --upgrade setuptools --no-cache-dir
     
RUN mkdir -p /app

COPY requirements.txt /app

COPY app /app

WORKDIR /app

RUN pip3 install -r requirements.txt
 
EXPOSE 8080
 
ENTRYPOINT ["/usr/bin/python3", "/app/voicy.py"]