# syntax=docker/dockerfile:1.7
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --default-timeout=300 -r requirements.txt

# Copy application code
COPY . .

ENV FLASK_APP=wsgi.py
ENV FLASK_RUN_HOST=0.0.0.0

EXPOSE 5000

CMD ["sh", "-c", "python init_db.py && flask run --host=0.0.0.0 --port=5000"]
