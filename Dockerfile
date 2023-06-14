FROM python:alpine

LABEL org.opencontainers.image.authors="Morteza Karimi <morteza.k@bugloos.com>"
LABEL org.opencontainers.image.title="Supervisord Docker"
LABEL org.opencontainers.image.vendor="Bugloos"
LABEL org.opencontainers.image.version="1.0.0"
LABEL maintainer="Morteza Karimi <morteza.k@bugloos.com>"

COPY requirements.txt requirements.txt
RUN apk add --update --no-cache supervisor docker openrc && pip install -r requirements.txt
RUN rc-update add docker boot

ENV DOCKER_HOST=unix://var/run/docker.sock
RUN mkdir -p /etc/supervisor.d/

COPY config-generator.ini /etc/supervisor.d/config-generator.ini
COPY generate_config.py /usr/local/bin/generate_config
COPY supervisor_reloader.py /usr/local/bin/supervisor_reloader

RUN chmod +x /usr/local/bin/generate_config
RUN chmod +x /usr/local/bin/supervisor_reloader

CMD ["/usr/bin/supervisord","-n", "-c","/etc/supervisord.conf"]
