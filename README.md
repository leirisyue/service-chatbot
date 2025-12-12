Truy cập API tại: http://localhost:8000

Truy cập Swagger UI tại: http://localhost:8000/docs

### 1. Tạo môi trường
```bash
python -m venv .venv  
.venv\Scripts\activate
```

### 2. Build lại image từ Dockerfile (không dùng cache)
```bash
docker-compose build --no-cache
```
### 4. Khởi động với Docker Compose 
```bash
docker-compose up
# or
docker-compose up -d
# or
docker-compose up --build
```

# fix error
sau khi install thư viện tắt VSCode chạy lại bước 1

### Kiểm tra logs
```bash
docker-compose logs -f rag-service
```



```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent" \
  -H 'Content-Type: application/json' \
  -H 'X-goog-api-key: AIzaSyBrbHN9A6FP65H5_luoXCPpO0w72vC0kWI' \
  -X POST \
  -d '{
    "contents": [
      {
        "parts": [
          {
            "text": "Explain how AI works in a few words"
          }
        ]
      }
    ]
  }'
```
