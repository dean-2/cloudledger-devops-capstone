FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r appgroup && useradd -r -g appgroup -d /app -s /sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools>=78.1.1 wheel msgpack>=1.2.1 urllib3>=2.8.0 && \
    pip install --no-cache-dir --upgrade -r requirements.txt && \
    rm -rf /usr/local/lib/python*/ensurepip \
           /usr/local/lib/python*/site-packages/pip* \
           /root/.cache

COPY . .

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
