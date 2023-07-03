# syntax = docker/dockerfile:experimental

###--- BASE IMAGE ---###
FROM python:3.11.4-slim as base
ENV PYTHONIOENCODING=utf8 \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LC_CTYPE=C.UTF-8 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_NO_INTERACTION=1 \
    POETRY_VERSION=1.3.2 \
    VIRTUAL_ENV=/venv

###--- BUILDER IMAGE ---###
FROM base as builder
RUN apt update && apt install -y curl
RUN curl -sSL https://install.python-poetry.org | python -
RUN python -m venv /venv
ADD pyproject.toml poetry.lock ./
RUN ls ${POETRY_HOME} && \
    ${POETRY_HOME}/bin/poetry install --only=main --no-root

###--- RUNTIME IMAGE ---###
FROM builder as runtime
COPY --from=builder /venv /venv
ENV PATH=/venv/bin:$PATH
COPY . ./harvester
ENTRYPOINT ["poetry", "run", "python", "harvester/app.py"]