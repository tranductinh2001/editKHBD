# Beeknoee AI Configuration Guide (Chuẩn Hoá Tích Hợp Dự Án)

> **Lưu ý cập nhật quan trọng (2026)**:
> - Model cũ `google/gemini-2.5-flash-lite` và `gemini-2.5-flash-lite` **đã bị nhà cung cấp Beeknoee vô hiệu hóa / xóa bỏ**, gọi API sẽ báo lỗi:
>   `⚠️ HTTP 404: Model "google/gemini-2.5-flash-lite" không tồn tại hoặc đã bị vô hiệu. Dùng GET /v1/models để xem danh sách model.`
> - **Model thay thế khuyến nghị chính thức**: `google/gemini-3.1-flash-lite` (hoặc `gemini-3.1-flash-lite`).
> - Tốc độ phản hồi cực nhanh, chi phí siêu rẻ, tối ưu bóc tách văn bản, JSON và xử lý tài liệu giáo án/văn bản hành chính.

---

## 1. Danh Sách Model Beeknoee Hỗ Trợ Hiện Tại

| ID Model (API Call) | Tên hiển thị | Nhà phát triển | Đặc điểm & Khuyến nghị |
| :--- | :--- | :--- | :--- |
| **`google/gemini-3.1-flash-lite`** *(Mặc định)* | Google Gemini 3.1 Flash Lite | Google | **Tối ưu nhất**: Cực nhanh, tiết kiệm token, phù hợp OCR, phân tích JSON, bóc tách kịch bản/PPCT. |
| **`google/gemini-3.5-flash-lite`** | Gemini 3.5 Flash Lite | Google | Thế hệ mới 3.5, độ trễ cực thấp, suy luận văn phong nhanh. |
| **`google/gemini-3.5-flash`** | Gemini 3.5 Flash | Google | Cân bằng chất lượng & tốc độ, phù hợp viết chi tiết giáo án. |
| **`google/gemini-3.1-pro-preview`** | Gemini 3.1 Pro Preview | Google | Suy luận chuyên sâu, giải toán, xử lý logic phức tạp. |
| **`deepseek/deepseek-v4-flash`** | DeepSeek V4 Flash | DeepSeek | Phản hồi tiếng Việt tốt, chi phí rẻ. |

> 💡 **Cách kiểm tra danh sách Model còn sống từ Beeknoee bất cứ lúc nào:**
> ```bash
> curl -X GET "https://platform.beeknoee.com/api/v1/models" \
>   -H "Authorization: Bearer sk-bee-xxxx"
> ```

---

## 2. Cấu Hình Biến Môi Trường (.env)

```env
# ========================================================
# BEEKNOEE AI PLATFORM CONFIGURATION
# ========================================================
BEE_API_KEY=sk-bee-73e9d744f8ef96f61278f28f4acfc8e44b69ee94c9cf6714720044f8c91c8502
BEE_BASE_URL=https://platform.beeknoee.com/api/v1
AI_MODEL=google/gemini-3.1-flash-lite

# Định danh phụ (tương thích cho các thư viện khác nhau)
BEEKNOEE_API_KEY=sk-bee-73e9d744f8ef96f61278f28f4acfc8e44b69ee94c9cf6714720044f8c91c8502
BEEKNOEE_BASE_URL=https://platform.beeknoee.com/api/v1
VISION_MODEL=google/gemini-3.1-flash-lite
AI_TIMEOUT=90000
```

---

## 3. Cấu Hình JSON Cho Ứng Dụng (`config.json`)

```json
{
  "ai_config": {
    "enabled": true,
    "base_url": "https://platform.beeknoee.com/api/v1",
    "api_key": "sk-bee-xxxx",
    "model": "google/gemini-3.1-flash-lite",
    "auto_format_title": true,
    "add_nls": true,
    "format_5512": true
  }
}
```

---

## 4. Tích Hợp TypeScript / Next.js / React

### `src/lib/config.ts`
```typescript
import { z } from 'zod';

export const aiConfigSchema = z.object({
  provider: z.string().default('beeknoee'),
  baseUrl: z.string().default('https://platform.beeknoee.com/api/v1'),
  apiKey: z.string().default(process.env.BEE_API_KEY || ''),
  model: z.string().default('google/gemini-3.1-flash-lite'),
  visionModel: z.string().default('google/gemini-3.1-flash-lite'),
  timeout: z.coerce.number().default(90000),
});

export type AIConfig = z.infer<typeof aiConfigSchema>;
```

### `src/lib/ai-models.ts`
```typescript
export interface AIModelConfig {
  id: string;
  displayName: string;
  provider: string;
  isActive: boolean;
  sortOrder: number;
}

export const AI_MODELS: AIModelConfig[] = [
  {
    id: 'google/gemini-3.1-flash-lite',
    displayName: 'Google Gemini 3.1 Flash Lite (Khuyên dùng)',
    provider: 'Google',
    isActive: true,
    sortOrder: 1,
  },
  {
    id: 'google/gemini-3.5-flash-lite',
    displayName: 'Gemini 3.5 Flash Lite',
    provider: 'Google',
    isActive: true,
    sortOrder: 2,
  },
  {
    id: 'google/gemini-3.5-flash',
    displayName: 'Gemini 3.5 Flash',
    provider: 'Google',
    isActive: true,
    sortOrder: 3,
  },
  {
    id: 'google/gemini-3.1-pro-preview',
    displayName: 'Gemini 3.1 Pro Preview (Suy luận sâu)',
    provider: 'Google',
    isActive: true,
    sortOrder: 4,
  }
];

export function getDefaultModel(): string {
  return 'google/gemini-3.1-flash-lite';
}
```

---

## 5. Client Python Hoàn Chỉnh (`beeknoee_client.py`)

Có sẵn cơ chế **tự động chuyển đổi các model cũ** (`gemini-2.5-flash-lite`) sang `google/gemini-3.1-flash-lite` để tránh lỗi 404:

```python
import os
import requests
import json

DEFAULT_BASE_URL = "https://platform.beeknoee.com/api/v1"
DEFAULT_MODEL = "google/gemini-3.1-flash-lite"

# Bảng tự động ánh xạ model cũ/vô hiệu hóa sang model mới đang hoạt động
DEPRECATED_MODELS_MAP = {
    "gemini-2.5-flash-lite": "google/gemini-3.1-flash-lite",
    "google/gemini-2.5-flash-lite": "google/gemini-3.1-flash-lite",
    "gemini-2.5-flash": "google/gemini-3.5-flash",
    "google/gemini-2.5-flash": "google/gemini-3.5-flash",
    "gemini-2.5-pro": "google/gemini-3.1-pro-preview",
    "google/gemini-2.5-pro": "google/gemini-3.1-pro-preview",
}

class BeeknoeeClient:
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        self.api_key = api_key or os.environ.get("BEE_API_KEY")
        self.base_url = (base_url or os.environ.get("BEE_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")
        raw_model = model or os.environ.get("AI_MODEL") or DEFAULT_MODEL
        self.model = DEPRECATED_MODELS_MAP.get(raw_model, raw_model)

    def chat(self, prompt: str, system_prompt: str = None, temperature: float = 0.2, max_tokens: int = 4096) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=90
        )

        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Beeknoee API Error (HTTP {resp.status_code}): {resp.text}")

    def chat_json(self, prompt: str, system_prompt: str = None) -> dict:
        """Gọi AI và tự động làm sạch Markdown (```json ... ```) để trả về dict"""
        content = self.chat(prompt, system_prompt=system_prompt)
        cleaned = content.strip()
        if "```json" in cleaned:
            cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned:
            cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()
        return json.loads(cleaned)
```

---

## 6. Lệnh Kiểm Tra Nhanh (cURL & Python)

### Kiểm tra bằng cURL:
```bash
curl -X POST "https://platform.beeknoee.com/api/v1/chat/completions" \
  -H "Authorization: Bearer sk-bee-73e9d744f8ef96f61278f28f4acfc8e44b69ee94c9cf6714720044f8c91c8502" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-3.1-flash-lite",
    "messages": [
      {"role": "user", "content": "Phản hồi BEEKONE_OK"}
    ],
    "temperature": 0.1
  }'
```

### Kiểm tra bằng Python một dòng:
```bash
python -c "import requests; r=requests.post('https://platform.beeknoee.com/api/v1/chat/completions', headers={'Authorization': 'Bearer sk-bee-73e9d744f8ef96f61278f28f4acfc8e44b69ee94c9cf6714720044f8c91c8502', 'Content-Type': 'application/json'}, json={'model': 'google/gemini-3.1-flash-lite', 'messages': [{'role': 'user', 'content': 'Hello'}]}); print('HTTP', r.status_code, r.json()['choices'][0]['message']['content'])"
```
