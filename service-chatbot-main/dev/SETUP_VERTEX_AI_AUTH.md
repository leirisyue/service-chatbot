# Setup Vertex AI Authentication - Application Default Credentials

## Bước 1: Cài đặt Google Cloud CLI

Tải và cài đặt từ: https://cloud.google.com/sdk/docs/install

## Bước 2: Login và setup credentials

Mở PowerShell/Terminal và chạy:

```powershell
# Login vào Google Cloud
gcloud auth application-default login

# Set project ID (thay YOUR_PROJECT_ID bằng project ID thật)
gcloud config set project aa-aibuild
```

Khi chạy lệnh trên, một cửa sổ browser sẽ mở để bạn login. Sau khi login thành công, credentials sẽ được lưu tự động.

## Bước 3: Kiểm tra credentials

```powershell
# Xem credentials location
gcloud auth application-default print-access-token
```

Credentials thường được lưu tại:
- Windows: `%APPDATA%\gcloud\application_default_credentials.json`
- Linux/Mac: `~/.config/gcloud/application_default_credentials.json`

## Bước 4: Enable Vertex AI API

```powershell
gcloud services enable aiplatform.googleapis.com
```

## Bước 5: Test authentication

Chạy script test:

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe test_vertex_ai.py
```

---

## Giải pháp thay thế: Sử dụng Service Account Key

Nếu không thể dùng `gcloud auth`, bạn có thể tạo Service Account key:

### 1. Tạo Service Account

Truy cập Google Cloud Console → IAM & Admin → Service Accounts → Create Service Account

- Name: `gemini-chatbot-sa`
- Grant roles:
  - `Vertex AI User`
  - `Generative AI User`

### 2. Tạo và download key

- Click vào Service Account vừa tạo
- Keys tab → Add Key → Create new key → JSON
- Lưu file JSON vào: `D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json`

### 3. Set environment variable

**Option A: Trong code (config.py):**

```python
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json'
```

**Option B: Trong .env file:**

```env
GOOGLE_APPLICATION_CREDENTIALS=D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json
```

**Option C: System environment variable (PowerShell):**

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json"
```

Để set permanent:
```powershell
[System.Environment]::SetEnvironmentVariable('GOOGLE_APPLICATION_CREDENTIALS', 'D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json', 'User')
```

---

## Khuyến nghị

✅ **Dùng gcloud auth** (Bước 1-5) - Đơn giản nhất, an toàn nhất

⚠️ **Dùng Service Account key** - Chỉ khi không thể dùng gcloud auth

---

## Troubleshooting

### Lỗi: "Your default credentials were not found"

→ Chạy: `gcloud auth application-default login`

### Lỗi: "Permission denied"

→ Đảm bảo user/service account có role `Vertex AI User`

### Lỗi: "API not enabled"

→ Chạy: `gcloud services enable aiplatform.googleapis.com`

---

## Sau khi setup xong

Test lại ứng dụng:

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe test_vertex_ai.py
```

Nếu thành công, bạn có thể chạy chatbot:

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe chatbot_api.py
```
