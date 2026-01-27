# Hướng dẫn sửa lỗi Gemini API

## Vấn đề
Bạn đang gặp lỗi xác thực vì:
1. Code đang cố sử dụng API key với models yêu cầu OAuth (Vertex AI)
2. Có conflict giữa `google-generativeai` và `google-cloud-aiplatform`

## Giải pháp: Sử dụng Google AI Studio API (khuyến nghị)

### Bước 1: Uninstall Vertex AI package
```bash
pip uninstall google-cloud-aiplatform -y
```

### Bước 2: Reinstall google-generativeai
```bash
pip uninstall google-generativeai -y
pip install --upgrade google-generativeai
```

### Bước 3: Kiểm tra API key
- Đảm bảo API key của bạn được tạo từ **Google AI Studio** (https://makersuite.google.com/app/apikey)
- KHÔNG phải từ Google Cloud Console

### Bước 4: Sửa model names
Thay tất cả `gemini-2.5-flash` thành `gemini-1.5-flash` hoặc `gemini-1.5-pro`

**Lý do**: Model `gemini-2.5-flash` chỉ khả dụng trên Vertex AI (cần OAuth), không hỗ trợ API key.

### Bước 5: Test lại
```bash
python test_gemini_api.py
```

---

## Giải pháp thay thế: Sử dụng Vertex AI (phức tạp hơn)

Nếu bạn muốn dùng `gemini-2.5-flash`, bạn cần setup Vertex AI:

### Bước 1: Tạo Service Account
```bash
gcloud iam service-accounts create gemini-sa --display-name="Gemini Service Account"
```

### Bước 2: Grant permissions
```bash
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:gemini-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

### Bước 3: Download key
```bash
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=gemini-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Bước 4: Set environment variable
```bash
set GOOGLE_APPLICATION_CREDENTIALS=path\to\service-account-key.json
```

### Bước 5: Sử dụng Vertex AI trong code
```python
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(project="YOUR_PROJECT_ID", location="us-central1")
model = GenerativeModel("gemini-2.5-flash")
```

---

## Khuyến nghị của tôi

**Sử dụng giải pháp 1** (Google AI Studio) vì:
- Đơn giản hơn (chỉ cần API key)
- Không cần setup Service Account
- Đủ cho hầu hết use cases
- Models `gemini-1.5-pro` và `gemini-1.5-flash` rất mạnh

Nếu cần model `gemini-2.5-flash` bắt buộc, hãy dùng giải pháp 2.
