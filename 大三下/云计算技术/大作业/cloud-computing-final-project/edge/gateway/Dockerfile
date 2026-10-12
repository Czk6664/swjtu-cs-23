ARG PYTHON_IMAGE=docker.m.daocloud.io/library/python:3.11-slim

FROM ${PYTHON_IMAGE}
WORKDIR /app

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ENV PIP_INDEX_URL=${PIP_INDEX_URL}
ENV PIP_NO_CACHE_DIR=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY mqtt_to_redis.py .
CMD ["python", "mqtt_to_redis.py"]
