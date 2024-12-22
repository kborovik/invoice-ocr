FROM python:3.12-slim as base

LABEL org.opencontainers.image.source="https://github.com/kborovik/coroil-ocrinv"
LABEL org.opencontainers.image.description="Google Cloud Platform - Document AI - Invoice OCR"
LABEL org.opencontainers.image.licenses="MIT"

ENV debian_frontend=noninteractive

RUN apt update -y && apt install -y curl

FROM base as build

ARG VERSION

COPY llmdoc-${VERSION}-py3-none-any.whl /tmp/llmdoc-${VERSION}-py3-none-any.whl

RUN pip install --no-cache-dir /tmp/llmdoc-${VERSION}-py3-none-any.whl

ENTRYPOINT [ "uvicorn", "llmdoc.api_v1:app", "--interface=wsgi", "--host=0.0.0.0", "--no-access-log"]