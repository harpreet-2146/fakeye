FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN apt-get update && apt-get install -y build-essential libssl-dev libxml2-dev libxslt1-dev libjpeg-dev curl
RUN pip install --no-cache-dir -r requirements.txt

# Playwright browsers
RUN playwright install --with-deps

COPY ./app /app

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
