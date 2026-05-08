FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/state && mkdir -p state

# state/ aponta para o volume persistente via symlink criado no start
EXPOSE 8787

CMD ["python", "start_cloud.py"]
