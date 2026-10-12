# syntax=docker/dockerfile:1

ARG PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim

FROM ${PYTHON_IMAGE} AS builder
WORKDIR /build

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --target /build/packages

FROM ${PYTHON_IMAGE}
WORKDIR /app

ENV PYTHONPATH=/app/packages
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=production

COPY --from=builder /build/packages /app/packages
COPY app.py .

EXPOSE 5000
CMD ["python", "app.py"]
