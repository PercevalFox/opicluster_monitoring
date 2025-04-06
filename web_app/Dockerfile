FROM python:3.9-slim
WORKDIR /app
RUN useradd -m -s /usr/sbin/nologin appuser && \
    mkdir -p /tmp && \
    chown appuser:appuser /tmp /app && \
    chmod 700 /app /tmp
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
USER appuser
COPY --chown=appuser:appuser . .
EXPOSE 5000
CMD ["python", "app.py"]
