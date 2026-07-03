FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ app/

RUN mkdir -p uploads outputs

EXPOSE 8000

# Render (and most PaaS) inject PORT; fall back to 8000 for local runs
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
