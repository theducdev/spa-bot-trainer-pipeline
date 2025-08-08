# 🧐 Spa-Bot Trainer Pipeline

Pipeline tự động huấn luyện và triển khai chatbot Spa-Bot sử dụng dữ liệu từ Google Sheets, fine-tune và thông báo qua Telegram, deploy qua Ollama, giao diện truy cập qua OpenWebUI.

---

## 🎯 Mục tiêu

Tự động hóa toàn bộ quy trình huấn luyện - deploy mô hình - gắn API - kết nối giao diện chat.

---

## 🛠️ Tech Stack

| Thành phần                      | Công dụng                             |
| ------------------------------- | ------------------------------------- |
| Google Sheets API / Apps Script | Gối trigger khi nhập dữ liệu mới      |
| Python Scripts                  | Xử lý và chuyển đổi dữ liệu           |
| Docker Compose                  | Quản lý và triển khai các services    |
| LLaMA-Factory                   | Framework fine-tune mô hình ngôn ngữ  |
| Ollama                          | Deploy local mô hình LLM              |
| OpenWebUI                       | Frontend giao diện chat trực quan     |
| Telegram Bot                    | Gửi thông báo khi training xong       |

---

## 📊 Cấu trúc dữ liệu training

### Google Sheets Template

Dữ liệu training được nhập vào Google Sheets với cấu trúc sau:
[Template Sheet](https://docs.google.com/spreadsheets/d/1c2SeE68VOcsFiaGxuRRccHYAddVXaY8QwzQqC2ld26k/edit?gid=0)

| Column          | Mô tả                           | Ví dụ                                          |
| --------------- | ------------------------------- | ---------------------------------------------- |
| user_message    | Câu hỏi/yêu cầu của khách      | "Xin chào", "Tôi muốn đặt lịch massage"       |
| assistant_message| Câu trả lời của bot            | "Chào bạn! Bạn muốn đặt dịch vụ spa nào?"     |
| sent            | Trạng thái đã xử lý            | TRUE/FALSE                                     |

### Định dạng JSONL cho training

Dữ liệu từ Google Sheets sẽ được chuyển đổi sang định dạng JSONL với cấu trúc:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Câu hỏi của người dùng"
    },
    {
      "role": "assistant", 
      "content": "Câu trả lời của bot"
    }
  ]
}
```

Ví dụ nội dung file training.jsonl:
```json
{"messages": [{"role": "user", "content": "Giá gói chăm sóc da là bao nhiêu?"}, {"role": "assistant", "content": "Gói chăm sóc da hiện có giá 500.000đ cho 60 phút."}]}
{"messages": [{"role": "user", "content": "Có khuyến mãi gì không?"}, {"role": "assistant", "content": "Dạ hiện tại chúng tôi có giảm 20% cho khách hàng mới trong tháng này."}]}
```

---

## 🔹 Các bước trong pipeline

### 1. Thu thập dữ liệu từ Google Sheets

* Google Apps Script theo dõi thay đổi và trigger webhook
* Script Python xử lý và chuyển đổi dữ liệu

### 2. Chuẩn bị dữ liệu training

* Dữ liệu được chuyển đổi tự động từ Google Sheets sang `.jsonl`
* Mỗi cặp hội thoại được format theo chuẩn messages với role user/assistant
* File được lưu trong thư mục `data/` với timestamp

### 3. Fine-tune mô hình

* Sử dụng LLaMA-Factory với config được định nghĩa trong `configs/fine_tune_spa.yaml`
* Training được thực hiện trong container Docker

### 4. Deploy mô hình

* Tạo và cập nhật model trong Ollama:
```bash
ollama create spa-bot -f ollama/Modelfile
```

### 5. Kết nối giao diện

* OpenWebUI được cấu hình để kết nối với Ollama endpoint
* Giao diện chat trực quan để tương tác với model

### 6. Thông báo hoàn thành

* Bot Telegram gửi thông báo khi quá trình hoàn tất:
```text
✅ Đã fine-tune và tạo model Spa-Bot thành công!
```

---

## 📁 Cấu trúc project

```
spa-bot-trainer-pipeline/
├── configs/                  # Cấu hình cho fine-tuning và chatbot
│   ├── chatbot_config.json
│   └── fine_tune_spa.yaml
├── data/                    # Dữ liệu training và logs
│   ├── logs/
│   ├── training.jsonl
│   └── uploads/
├── mcp-server/             # Server quản lý API
├── ollama/                 # Cấu hình Ollama model
│   └── Modelfile
├── open-webui/            # Giao diện người dùng
├── scripts/               # Các script xử lý
│   ├── google-appscript.js
│   ├── main.py
│   ├── log_manager.py
│   └── telegram_notifier.py
└── docker-compose.yml     # Cấu hình Docker services
```

---

## 🚫 Yêu cầu hệ thống

| Thành phần    | Yêu cầu                                      |
| ------------- | -------------------------------------------- |
| Docker & Compose | Đã cài đặt và chạy daemon                    |
| Python        | Version 3.8+ với các package trong requirements.txt |
| GPU           | CUDA compatible cho fine-tuning              |
| Ollama        | Cài đặt local                               |
| OpenWebUI     | Có thể kết nối được với Ollama              |
| Telegram Bot  | Token và Chat ID đã cấu hình                |

---

## 🚀 Hướng dẫn cài đặt

### 1. Cài đặt môi trường
```bash
# Clone repository
git clone <repository_url>
cd spa-bot-trainer-pipeline

# Cài đặt dependencies
pip install -r requirements.txt
```

### 2. Build và chạy OpenWebUI
```bash
# Di chuyển vào thư mục open-webui
cd open-webui

# Build Docker image
docker build -t open-webui:latest .

# Chạy container
docker run -it --rm -p 8080:8080 open-webui:latest

# Hoặc chạy với cấu hình database (thay thế các giá trị phù hợp)
docker run -it -p 8080:8080 \
  -e DB_HOST=<host> \
  -e DB_USER=<user> \
  -e DB_PASSWORD=<password> \
  -e DB_NAME=<dbname> \
  -e DB_PORT=<port> \
  -e DB_TYPE=postgresql \
  open-webui:latest
```

### 3. Chạy giao diện chat
```bash
docker-compose up -d
```

### 4. Chạy giao diện pipeline-training
```bash
python scripts/main.py
```

### 4. Truy cập giao diện

- Mở trình duyệt và truy cập: `http://localhost:8080`
- Đăng nhập và chọn model `spa-bot` để bắt đầu chat

- Mở trình duyệt và truy cập: `http://localhost:5000`
- Giao diện pipeline-training hiện ra và bắt đầu thao tác

---

