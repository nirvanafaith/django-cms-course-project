FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH

RUN python -m pip install --no-cache-dir uv==0.8.8
RUN python -m venv "${VIRTUAL_ENV}"

WORKDIR /app
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python "${VIRTUAL_ENV}/bin/python" --requirement requirements.txt

FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    WAITRESS_HOST=0.0.0.0 \
    WAITRESS_PORT=8000

ARG UID=10001
RUN adduser --disabled-password --gecos "" --home /nonexistent \
    --shell /usr/sbin/nologin --no-create-home --uid "${UID}" cms \
    && mkdir -p /app/logs \
    && chown "${UID}:${UID}" /app/logs

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY . .

RUN DJANGO_TEST=1 \
    POSTGRES_DB=build \
    POSTGRES_USER=build \
    POSTGRES_PASSWORD=build \
    python manage.py collectstatic --noinput

EXPOSE 8000
USER cms

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live/', timeout=3)"]

CMD ["python", "manage.py", "serve_waitress"]
