FROM python:3.11-slim

WORKDIR /app

# Installiere System-Abhängigkeiten
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Kopiere Requirements zuerst für besseres Caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /scripts/logs
# Kopiere die gesamte App
COPY . .

# Exponiere den Port
EXPOSE 5000

# Startbefehl
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]