# 🧐 Spa-Bot Trainer Pipeline

Pipeline tự động huấn luyện và triển khai chatbot Spa-Bot sử dụng dữ liệu từ Google Sheets, fine-tune với LLaMA-Factory, deploy qua Ollama, giao diện truy cập qua OpenWebUI.

---

## 🎯 Mục tiêu

Tự động hóa toàn bộ quy trình huấn luyện - deploy mô hình - gắn API - kết nối giao diện chat.

---

## 🛠️ Tech Stack

| Thành phần                      | Công dụng                             |
| ------------------------------- | ------------------------------------- |
| Google Sheets API / Apps Script | Gối trigger khi nhập dữ liệu mới      |
| n8n                             | Tổ chức pipeline tự động              |
| Node.js Code Node               | Chuyển dữ liệu sang `.jsonl`          |
| Docker API / SSH                | Khởi chạy training bằng LLaMA-Factory |
| LLaMA-Factory                   | Framework fine-tune mô hình ngôn ngữ  |
| Ollama                          | Deploy local mô hình LLM              |
| OpenWebUI                       | Frontend giao diện chat trực quan     |
| Telegram Bot                    | Gửi thông báo khi training xong       |

---

## 🔹 Các bước trong pipeline

### 1. Trigger từ Google Sheets

* Nhập dòng dữ liệu: `{ instruction, input, output }`
* Apps Script gửi webhook n8n

### 2. Chuyển dữ liệu sang `.jsonl`

```json
{
  "instruction": "Câu hỏi",
  "input": "Thông tin bổ sung",
  "output": "Câu trả lời"
}
```

### 3. Khởi chạy fine-tune

* Qua Docker API hoặc SSH:

```bash
docker exec -it llama_factory python src/train.py configs/fine_tune_spa.yaml
```

### 4. Theo dõi logs

* Nếu thấy "Training complete" thì chuyển tiếp.

### 5. Tạo model trong Ollama

```bash
ollama create spa-bot -f /path/to/Modelfile
```

### 6. Cập nhật endpoint

* Gán API hoặc chỉnh JSON config trong OpenWebUI để trỏ sang model mới

### 7. Thông báo qua Telegram

```text
✅ Dã fine-tune và tạo model Spa-Bot thành công!
```

---

## 💬 Giao diện chat với OpenWebUI

* Kết nối trực tiếp Ollama để chat với model `spa-bot`
* Cài đặt mỏ Ollama endpoint và chọn model trong UI

---

## 🚫 Yêu cầu hệ thống

| Thành phần    | Yêu cầu                                      |
| ------------- | -------------------------------------------- |
| Docker daemon | Cho phép truy cập API hoặc SSH               |
| LLaMA-Factory | GPU bật, mount volume `/data`, `/configs`    |
| Ollama        | Cài sẵn, chạy local                          |
| OpenWebUI     | Cài trên cùng máy hoặc có thể kết nối Ollama |
| Telegram Bot  | Token, Chat ID sẵn sàng                      |

---

## 📁 Cấu trúc repo (dự kiến)

```
spa-bot-trainer-pipeline/
├── README.md
├── scripts/
│   ├── convert-to-jsonl.js
│   └── update-endpoint.js
├── config/
│   └── Modelfile
├── n8n-workflow/
│   └── spa-bot-fine-tune.json
```

---

## 📢 Góp ý / Liên hệ

* Mở Issue / PR để bổ sung
* Hoặc gửi Telegram cho bot khi bạn muốn re-train
