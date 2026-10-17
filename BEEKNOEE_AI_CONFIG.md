# Beeknoee AI Configuration

## Source: `src/lib/config.ts` + `src/lib/beeknoee.ts` + `src/lib/beekone-ai-client.ts`

---

## 1. Environment Variables

```env
# Beeknoee AI
BEE_API_KEY=sk-bee-xxxx
BEE_BASE_URL=https://platform.beeknoee.com/api/v1

# Alternative env names (some code uses these)
GEMINI_API_KEY=sk-bee-xxxx
BEEKNOEE_API_KEY=sk-bee-xxxx
BEEKNOEE_BASE_URL=https://platform.beeknoee.com/api/v1
```

---

## 2. API Endpoint

```typescript
// Chat Completions
POST https://platform.beeknoee.com/api/v1/chat/completions

// Headers
Authorization: Bearer <BEE_API_KEY>
Content-Type: application/json
```

---

## 3. TypeScript Config (`config.ts`)

```typescript
const aiSchema = z.object({
  provider: z.string().default('beeknoee'),
  model: z.string().default('gemini-3.1-flash-lite'),
  apiKey: z.string().default(''),
  baseUrl: z.string().default('https://platform.beeknoee.com'),
  visionModel: z.string().default('google/gemini-2.5-flash-lite'),
  timeout: z.coerce.number().default(120000),
});
```

---

## 4. AI Models (`ai-models.ts`)

```typescript
export const AI_MODELS: AIModelConfig[] = [
  {
    id: 'gemini-2.5-flash-lite',
    displayName: 'Gemini 2.5 Flash Lite',
    provider: 'Gemini',
    inputPrice: 0.10,
    outputPrice: 0.40,
    unit: 'USD / 1M Tokens',
    isActive: true,
    sortOrder: 1,
  },
  {
    id: 'google/gemini-2.5-flash-lite',
    displayName: 'Google Gemini 2.5 Flash Lite',
    provider: 'Google',
    inputPrice: 0.10,
    outputPrice: 0.40,
    unit: 'USD / 1M Tokens',
    isActive: true,
    sortOrder: 2,
  },
  {
    id: 'gemini-3.1-flash-lite',
    displayName: 'Gemini 3.1 Flash Lite',
    provider: 'Gemini',
    inputPrice: 0.25,
    outputPrice: 1.50,
    unit: 'USD / 1M Tokens',
    isActive: true,
    sortOrder: 3,
  },
  // ... more models
];

export function getDefaultModel(): AIModelConfig {
  return getActiveModels()[0];
}
```

---

## 5. Python Client Pattern

```python
import requests
import base64

class BeeknoeeClient:
    def __init__(self, api_key: str, base_url: str = "https://platform.beeknoee.com/api/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "gemini-2.5-flash-lite"

    def chat(self, prompt: str, system_prompt: str = None, temperature: float = 0.2, max_tokens: int = 8192) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120
        )

        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API Error: {resp.status_code} - {resp.text}")

    def chat_with_image(self, image_base64: str, prompt: str, mime_type: str = "image/png") -> str:
        payload = {
            "model": self.model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}}
                ]
            }],
            "temperature": 0.1,
            "max_tokens": 32000
        }

        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=180
        )

        if resp.status_code == 200:
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        else:
            raise Exception(f"API Error: {resp.status_code}")
```

---

## 6. Grading Prompt Template

```python
GRADING_PROMPT = """Bạn là giáo viên có kinh nghiệm 20 năm. Chấm giáo án theo rubric.

## GIÁO ÁN CẦN CHẤM:
{lesson_plan_text}

## RUBRIC (100 điểm):

### 1. MỤC TIÊU (15 điểm)
- Đủ 3 mặt (kiến thức, kỹ năng, thái độ): 5 điểm
- Cụ thể, đo được: 5 điểm
- Phù hợp: 5 điểm

### 2. CÁC HOẠT ĐỘNG (35 điểm)
- Đủ 3 giai đoạn: 10 điểm
- Rõ ràng, cụ thể: 10 điểm
- HS được hoạt động: 10 điểm
- Thời gian hợp lý: 5 điểm

### 3. HOẠT ĐỘNG GV (15 điểm)
- Hướng dẫn rõ: 5 điểm
- Câu hỏi tốt: 5 điểm
- Sử dụng CNTT: 5 điểm

### 4. HOẠT ĐỘNG HS (15 điểm)
- HS hoạt động: 5 điểm
- Hoạt động nhóm: 5 điểm
- Thực hành: 5 điểm

### 5. PHƯƠNG TIỆN (10 điểm)
- Đủ thiết bị: 5 điểm
- Phù hợp: 5 điểm

### 6. ĐÁNH GIÁ (10 điểm)
- Đa dạng: 5 điểm
- Đầy đủ: 5 điểm

## OUTPUT FORMAT:
{
  "total_score": 0-100,
  "scores": {
    "muc_tieu": {"score": 0-15, "detail": "..."},
    "hoat_dong": {"score": 0-35, "detail": "..."},
    "gv_action": {"score": 0-15, "detail": "..."},
    "hs_action": {"score": 0-15, "detail": "..."},
    "phuong_tien": {"score": 0-10, "detail": "..."},
    "danh_gia": {"score": 0-10, "detail": "..."}
  },
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": ["...", "..."],
  "grade": "A/B/C/D/F"
}
"""
```

---

## 7. Semantic Classification Prompt

```python
CLASSIFY_PROMPT = """Phan loai {n} doan trong giao an.

Labels BAT BUOC:
- SECTION_HEADER (tieu de)
- TEACHER_ACTION (GV lam gi)
- STUDENT_ACTION (HS lam gi)
- TEACHING_MATERIAL (hoc lieu)
- LEARNING_OUTCOME (ket qua)
- QUESTION (cau hoi)
- ASSESSMENT (danh gia)
- PRODUCT (san pham)
- OBJECTIVE (muc tieu)
- INSTRUCTION (huong dan)
- UNKNOWN

Tra ve JSON:
{{"labels": [{{"index": 0, "label": "TYPE"}}, ...]}}

Day la cac doan:
{paragraphs}
"""
```

---

## 8. Review System Prompt (from `beeknoee.ts`)

```typescript
const SYSTEM_PROMPT = `Bạn là chuyên gia đánh giá giáo án theo chuẩn Bộ Giáo dục Việt Nam. 
Nhiệm vụ của bạn là phân tích chi tiết nội dung giáo án và đưa ra nhận xét, góp ý cụ thể dưới dạng JSON.`;
```

---

## 9. Usage Example (Python)

```python
from beeknoee_client import BeeknoeeClient

# Initialize
client = BeeknoeeClient(
    api_key="sk-bee-xxxx",
    base_url="https://platform.beeknoee.com/api/v1"
)

# Simple chat
response = client.chat("Hello, explain AI")
print(response)

# With system prompt
response = client.chat(
    prompt="Cham giao an nay",
    system_prompt="Ban la giao vien 20 nam kinh nghiem"
)

# With image (for OCR)
with open("document.pdf", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()
    
response = client.chat_with_image(
    image_base64=image_b64,
    prompt="Trich xuat van ban tu tai lieu nay",
    mime_type="application/pdf"
)
```

---

## 10. .env Example

```env
# AI Provider
BEE_API_KEY=sk-bee-598e4c3d2043871a93574e80cb79833aab78cd2915e6b05caedd7c1ff5eea3f5
BEE_BASE_URL=https://platform.beeknoee.com/api/v1

# Optional: Override model
AI_MODEL=gemini-2.5-flash-lite
VISION_MODEL=gemini-2.5-flash-lite

# Optional: Timeout (ms)
AI_TIMEOUT=120000
```
