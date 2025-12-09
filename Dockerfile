FROM python:3.11-slim

# System deps for Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr tesseract-ocr-vie \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY app /app/app

ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Debug port for debugpy
EXPOSE 5678

# Start app under debugpy for VS Code attach
CMD ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "app.main"]