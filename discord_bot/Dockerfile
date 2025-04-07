FROM python:3.9-slim
ENV DEBIAN_FRONTEND=noninteractive
ENV TMPDIR=/var/tmp
WORKDIR /app
RUN useradd -m -s /usr/sbin/nologin appuser && \
    mkdir -p /tmp && \
    chown appuser:appuser /tmp /app && \
    chmod 700 /app /tmp
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl procps && \
    rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
USER appuser
COPY --chown=appuser:appuser . .
CMD ["python", "bot.py"]
