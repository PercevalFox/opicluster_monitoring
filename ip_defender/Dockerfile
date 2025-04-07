FROM python:3.9-slim

WORKDIR /app

COPY main.py .
COPY requirements.txt .

RUN apt-get update && apt-get install -y --no-install-recommends && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /var/lib/apt/lists/*

CMD ["python", "main.py"]
