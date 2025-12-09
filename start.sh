#!/bin/bash

echo "Starting RAG Chatbot Service..."

# Kiểm tra xem .env đã tồn tại chưa
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration and run again."
    exit 1
fi

# Build và khởi động Docker containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

echo "Service started! Access the API at http://localhost:8000"
echo "Swagger UI: http://localhost:8000/docs"