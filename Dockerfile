FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# App env
ENV FLASK_ENV=production
ENV PORT=8080

EXPOSE 8080

# Use app factory with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:create_app()", "--workers", "2"]




