# Hướng dẫn Fix lỗi xác thực Gemini API - GIẢI PHÁP HOÀN CHỈNH

## Vấn đề hiện tại

Bạn đang sử dụng API key không đúng định dạng. API key hiện tại bắt đầu bằng `AQ.Ab8...` có vẻ là từ Google Cloud, không hỗ trợ cho Gemini API.

## ✅ GIẢI PHÁP KHUYẾN NGHỊ: Sử dụng Google AI Studio API

### Bước 1: Tạo API Key mới từ Google AI Studio

1. Truy cập: https://aistudio.google.com/apikey  
2. Đăng nhập bằng tài khoản Google
3. Click **"Get API Key"** hoặc **"Create API Key"**
4. Chọn "Create API key in new project" hoặc chọn project existing
5. Copy API key (format: `AIza...`)

**Lưu ý quan trọng**: API key từ Google AI Studio có format bắt đầu bằng `AIza...` (không phải `AQ.Ab...`)

### Bước 2: Cập nhật file `.env`

Mở file `.env` và sửa:

```env
My_GOOGLE_API_KEY=AIzaSy...  # API key mới từ Google AI Studio
```

### Bước 3: Uninstall các package cũ và cài đặt package mới

```bash
# Uninstall old deprecated packages
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe -m pip uninstall google-generativeai google-cloud-aiplatform -y

# Install new google-genai package (đã được cài)
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe -m pip install --upgrade google-genai
```

### Bước 4: Update requirements.txt

Sửa file requirements.txt, thay:
```
google.generativeai
google-cloud-aiplatform
```

Thành:
```
google-genai>=1.60.0
```

### Bước 5: Test lại

```bash
D:/cty/3/code-main/service-chatbot-main-2/service-chatbot-main/.venv/Scripts/python.exe test_genai_new.py
```

---

## 🔄 GIẢI PHÁP THAY THẾ: Sử dụng Vertex AI (nếu bắt buộc)

Nếu bạn muốn tiếp tục dùng Vertex AI với model `gemini-2.5-flash`:

### Bước 1: Setup Google Cloud Project

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### Bước 2: Tạo Service Account

```bash
gcloud iam service-accounts create gemini-sa \
    --display-name="Gemini Service Account"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gemini-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=gemini-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Bước 3: Set environment variable

Trong Windows PowerShell:
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json"
```

Hoặc thêm vào file `.env`:
```env
GOOGLE_APPLICATION_CREDENTIALS=D:\cty\3\code-main\service-chatbot-main-2\service-chatbot-main\service-account-key.json
```

### Bước 4: Update code to use Vertex AI

Sửa imports:
```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project=settings.GOOGLE_PROJECT_ID, location=settings.GOOGLE_LOCATION)
model = GenerativeModel("gemini-2.5-flash")
```

---

## 🎯 KHUYẾN NGHỊ CỦA TÔI

**Sử dụng giải pháp 1** (Google AI Studio) vì:

✅ **Đơn giản**: Chỉ cần API key  
✅ **Miễn phí**: Free tier rộng rãi  
✅ **Nhanh**: Không cần setup phức tạp  
✅ **Đủ mạnh**: Models `gemini-1.5-pro`, `gemini-1.5-flash`, `gemini-2.0-flash-exp` rất tốt  

Chỉ dùng giải pháp 2 nếu:
- Bạn đã có Google Cloud project với billing enabled
- Cần models chỉ có trên Vertex AI
- Cần enterprise features (VPC, audit logs, v.v.)

---

## Sau khi fix xong

Code đã được tôi update để sử dụng models hỗ trợ API key:
- ✅ `textfunc.py`: Đã đổi sang `gemini-1.5-pro`
- ✅ `textapi_qwen.py`: Đã đổi sang `gemini-1.5-pro`
- ✅ `classifyapi.py`: Đã đổi sang `gemini-1.5-pro`

Bạn chỉ cần:
1. Tạo API key mới từ Google AI Studio
2. Update file `.env`
3. Test lại

---

## Tài liệu tham khảo

- Google AI Studio: https://aistudio.google.com/
- API Key Management: https://aistudio.google.com/apikey
- Google Genai SDK: https://googleapis.github.io/python-genai/
- Migration Guide: https://github.com/google-gemini/deprecated-generative-ai-python
