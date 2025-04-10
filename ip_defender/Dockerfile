FROM python:3.9-slim

WORKDIR /app

COPY main.py .
COPY requirements.txt .
COPY healthcheck.sh .

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

HEALTHCHECK --interval=5m --timeout=10s --start-period=1m --retries=3 CMD /app/healthcheck.sh

CMD ["python", "main.py"]
