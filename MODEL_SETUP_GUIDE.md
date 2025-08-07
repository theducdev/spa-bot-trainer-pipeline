# 🤖 Hướng dẫn Setup Model GPT-OSS 20B với Ollama

## 📋 Yêu cầu hệ thống

- **RAM**: Tối thiểu 32GB (khuyến nghị 64GB+)
- **GPU**: NVIDIA GPU với tối thiểu 24GB VRAM (khuyến nghị RTX 4090/A100)
- **Ổ cứng**: Tối thiểu 50GB trống
- **Docker**: Docker Desktop đã cài đặt và chạy
- **Python**: Python 3.9+ với pip

---

## 🚀 Bước 1: Cài đặt Ollama

### 1.1. Tải và cài Ollama

**Windows:**
```powershell
# Tải từ trang chủ: https://ollama.ai/download
# Hoặc dùng winget
winget install Ollama.Ollama
```

**macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 1.2. Khởi động Ollama service

```bash
# Khởi động Ollama
ollama serve

# Hoặc chạy như service (Linux/macOS)
sudo systemctl start ollama
```

---

## 📦 Bước 2: Tải Model GPT-OSS 20B

### 2.1. Tải model từ Ollama Hub

```bash
# Tải model GPT-OSS 20B
ollama pull gpt-oss:20b

# Kiểm tra model đã tải
ollama list
```

### 2.2. Hoặc tải từ Hugging Face (nếu cần)

```bash
# Nếu model chưa có trên Ollama Hub
git clone https://huggingface.co/microsoft/gpt-oss-20b
cd gpt-oss-20b

# Convert sang format Ollama
ollama create gpt-oss:20b -f Modelfile
```

---

## 🔧 Bước 3: Deploy Model trên Ollama

### 3.1. Tạo Modelfile tùy chỉnh (tùy chọn)

Tạo file `Modelfile` để cấu hình model:

```dockerfile
FROM gpt-oss:20b

# Cấu hình tham số
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER num_ctx 4096
PARAMETER num_predict 512

# System prompt cho spa
SYSTEM """
Bạn là trợ lý ảo chuyên nghiệp của spa. Nhiệm vụ của bạn là:
1. Trả lời các câu hỏi về dịch vụ, giá cả và lịch hẹn
2. Tư vấn dịch vụ phù hợp cho khách hàng  
3. Hỗ trợ đặt lịch và thông tin liên hệ
4. Trả lời bằng tiếng Việt, lịch sự và chuyên nghiệp
"""
```

### 3.2. Tạo model custom

```bash
# Tạo model với Modelfile tùy chỉnh
ollama create spa-gpt-oss:20b -f Modelfile

# Hoặc sử dụng model gốc
ollama pull gpt-oss:20b
```

### 3.3. Test model

```bash
# Test model hoạt động
ollama run gpt-oss:20b "Xin chào, bạn là ai?"

# Test với câu hỏi spa
ollama run gpt-oss:20b "Spa có những dịch vụ gì?"
```

---

## ⚙️ Bước 4: Cấu hình Environment Variables

### 4.1. Tạo/cập nhật file `.env`

Trong thư mục project, tạo file `.env`:

```env
# Ollama Configuration
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b

# Database Configuration
DB_DRIVER={SQL Server}
DB_SERVER=localhost
DB_DATABASE=SpaDB
DB_TRUSTED_CONNECTION=yes

# Embedding Model
EMBEDDING_MODEL=VoVanPhuc/sup-SimCSE-VietNamese-phobert-base
```

### 4.2. Cài đặt dependencies

```bash
# Cài thư viện Python cần thiết
pip install requests python-dotenv flask

# Hoặc từ requirements.txt
pip install -r requirements.txt
```

---

## 🔌 Bước 5: Tích hợp vào Code

### 5.1. Cấu trúc project

```
spa-bot-trainer-pipeline/
├── scripts/
│   ├── modules/
│   │   ├── query.py          # Đã có sẵn
│   │   └── retrived_rag.py   # Đã có sẵn
│   └── proxy.py              # Đã có sẵn
├── .env                      # Tạo mới
└── requirements.txt          # Tạo mới
```

### 5.2. Code đã được tích hợp

Model đã được tích hợp vào:
- **`modules/query.py`**: Xử lý RAG và gọi Ollama
- **`proxy.py`**: API endpoint cho chat
- **`.env`**: Cấu hình model và URL

### 5.3. Kiểm tra kết nối

```python
# Test script để kiểm tra kết nối
import requests

def test_ollama():
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "gpt-oss:20b",
                "prompt": "Xin chào",
                "stream": False
            },
            timeout=30
        )
        print("✅ Ollama hoạt động:", response.json()['response'])
    except Exception as e:
        print("❌ Lỗi:", e)

test_ollama()
```

---

## 🚀 Bước 6: Chạy Hệ thống

### 6.1. Khởi động các service

```bash
# Terminal 1: Khởi động Ollama
ollama serve

# Terminal 2: Khởi động Flask app
cd scripts
python proxy.py
```

### 6.2. Test hệ thống

```bash
# Test API endpoint
curl -X POST http://localhost:5000/bot-msg \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "msg=Thông tin khách hàng Nguyễn Thị Hoa"
```

### 6.3. Truy cập web interface

Mở trình duyệt: `http://localhost:5000`

---

## 🔧 Troubleshooting

### Lỗi thường gặp:

#### 1. **Model không tải được**
```bash
# Kiểm tra dung lượng
df -h

# Xóa model cũ nếu cần
ollama rm old-model
```

#### 2. **Timeout khi generate**
- Tăng timeout trong code (đã set 300s)
- Kiểm tra GPU memory: `nvidia-smi`
- Giảm context length trong Modelfile

#### 3. **Out of Memory**
```bash
# Kiểm tra RAM
free -h

# Restart Ollama
sudo systemctl restart ollama
```

#### 4. **Kết nối thất bại**
```bash
# Kiểm tra Ollama đang chạy
ps aux | grep ollama

# Kiểm tra port
netstat -an | grep 11434
```

---

## ⚡ Tips Tối ưu

### 1. **Tăng tốc độ**
- Sử dụng GPU có VRAM cao
- Set `num_gpu` trong Modelfile
- Giảm `num_ctx` nếu không cần context dài

### 2. **Tiết kiệm tài nguyên**
```bash
# Sử dụng quantized model
ollama pull gpt-oss:20b-q4_0  # 4-bit quantization
```

### 3. **Monitoring**
```bash
# Monitor GPU
watch nvidia-smi

# Monitor logs
ollama logs
```

---

## 📞 Hỗ trợ

- **Ollama Docs**: https://github.com/ollama/ollama
- **Model Info**: https://huggingface.co/microsoft/gpt-oss-20b
- **Issues**: Tạo issue trong repo này

---

## ✅ Checklist Setup

- [ ] Cài đặt Ollama
- [ ] Tải model gpt-oss:20b  
- [ ] Test model hoạt động
- [ ] Cấu hình file .env
- [ ] Cài Python dependencies
- [ ] Test API connection
- [ ] Chạy Flask app
- [ ] Test web interface
- [ ] Kiểm tra RAG pipeline

**🎉 Setup hoàn tất! Model đã sẵn sàng phục vụ.**
