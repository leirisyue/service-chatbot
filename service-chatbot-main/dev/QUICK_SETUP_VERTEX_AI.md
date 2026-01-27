# ⚡ HƯỚNG DẪN NHANH - Setup Vertex AI Authentication

## 🎯 Bạn cần làm gì?

Vertex AI yêu cầu **Application Default Credentials** (ADC) để xác thực. Có 2 cách:

---

## ✅ CÁCH 1: Sử dụng gcloud CLI (KHUYẾN NGHỊ - ĐƠN GIẢN NHẤT)

### Bước 1: Tải và cài đặt Google Cloud CLI

**Windows:**
- Download: https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe
- Chạy file installer
- Restart terminal sau khi cài xong

**Hoặc dùng Chocolatey:**
```powershell
choco install gcloudsdk
```

### Bước 2: Login và cấu hình

Mở **PowerShell mới** và chạy:

```powershell
# Login (sẽ mở browser)
gcloud auth application-default login

# Set project
gcloud config set project aa-aibuild

# Enable Vertex AI API
gcloud services enable aiplatform.googleapis.com
```

### Bước 3: Test

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe test_vertex_ai.py
```

✅ Nếu thấy "SUCCESS" - Hoàn tất!

---

## 🔑 CÁCH 2: Sử dụng Service Account Key (NẾU KHÔNG THỂ DÙNG GCLOUD)

### Bước 1: Tạo Service Account

1. Truy cập: https://console.cloud.google.com/iam-admin/serviceaccounts?project=aa-aibuild
2. Click **"Create Service Account"**
3. Điền thông tin:
   - **Name**: `gemini-chatbot-sa`
   - **Description**: `Service Account for Gemini Chatbot`
4. Click **"Create and Continue"**

### Bước 2: Cấp quyền

Chọn roles sau:
- ✅ **Vertex AI User** (`roles/aiplatform.user`)
- ✅ **Vertex AI Service Agent** (`roles/aiplatform.serviceAgent`)

Click **"Continue"** → **"Done"**

### Bước 3: Tạo và tải key

1. Click vào Service Account vừa tạo
2. Tab **"Keys"** → **"Add Key"** → **"Create new key"**
3. Chọn **JSON** → Click **"Create"**
4. File JSON sẽ được tải về

### Bước 4: Lưu file key

Di chuyển file JSON vào folder project và đổi tên:

```powershell
Move-Item ~\Downloads\aa-aibuild-*.json D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json
```

### Bước 5: Cấu hình environment variable

**Option A: Thêm vào file `.env`**

Mở file `.env` và thêm dòng:

```env
GOOGLE_APPLICATION_CREDENTIALS=D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json
```

**Option B: Set trong PowerShell (tạm thời)**

```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json"
```

**Option C: Set permanent (khuyến nghị)**

```powershell
[System.Environment]::SetEnvironmentVariable('GOOGLE_APPLICATION_CREDENTIALS', 'D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json', 'User')
```

Sau đó **restart terminal**.

### Bước 6: Test

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe test_vertex_ai.py
```

✅ Nếu thấy "SUCCESS" - Hoàn tất!

---

## ⚠️ Lưu ý bảo mật

Nếu dùng Service Account Key:

1. ❌ **KHÔNG commit** file `service-account-key.json` lên Git
2. ✅ Đã thêm vào `.gitignore`:
   ```
   service-account-key.json
   ```
3. ✅ Giữ file key an toàn, không share

---

## 🐛 Troubleshooting

### Lỗi: "Your default credentials were not found"

→ Chưa setup credentials. Làm theo Cách 1 hoặc Cách 2 ở trên.

### Lỗi: "Permission denied" hoặc "403"

→ Service Account chưa có đủ quyền. Vào IAM và add role **Vertex AI User**.

### Lỗi: "API not enabled"

→ Chạy: 
```powershell
gcloud services enable aiplatform.googleapis.com --project=aa-aibuild
```

### Lỗi: "Project not found"

→ Kiểm tra project ID trong file `.env`:
```env
GOOGLE_PROJECT_ID=aa-aibuild
```

---

## ✅ Sau khi setup xong

Chạy lại chatbot:

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe chatbot_api.py
```

hoặc

```powershell
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe -m uvicorn chatbot_api:app --reload
```

---

## 📞 Cần hỗ trợ thêm?

Xem file chi tiết: [SETUP_VERTEX_AI_AUTH.md](SETUP_VERTEX_AI_AUTH.md)
