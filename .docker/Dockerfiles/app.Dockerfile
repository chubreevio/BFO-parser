FROM python:3.14-slim-bookworm
ARG APP_ROOT

WORKDIR ${APP_ROOT}

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

## Установка пакетов из корпоративного прокси nexus
COPY .docker/etc/apt/sources.list /etc/apt/sources.list

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        # default-libmysqlclient-dev \
        pkg-config && \
    rm -rf /var/lib/apt/lists/*

## Установка pip пакетов из корпоративного прокси nexus
COPY .docker/etc/pip/pip.conf /etc/pip.conf

COPY alembic.ini .

COPY requirements.txt ./
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt