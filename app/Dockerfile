FROM ubuntu:18.04
LABEL "com.cupcake.vendor"="MrLicorice"

ENV DOCKER 1
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Rome
RUN echo $TZ > /etc/timezone

RUN useradd -ms /bin/bash app
COPY --chown=app:app . /app

RUN apt update && apt -y upgrade && apt -y install locales tzdata lib32z1 nano python3 python3-pip supervisor mysql-client libmysqlclient-dev
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
RUN dpkg-reconfigure -f noninteractive tzdata
RUN pip3 install -r /app/requirements.txt
RUN chown -R app:app /app

## Setup SSH Access
#RUN apt update && apt -y install openssh-server && mkdir /run/sshd

#VOLUME ["/app/db"]

ENTRYPOINT ["/usr/bin/supervisord", "-c", "/config/supervisor/supervisord.conf"]
