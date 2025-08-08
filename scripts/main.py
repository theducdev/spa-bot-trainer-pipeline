from flask import Flask, request, jsonify, render_template, Response
import pandas as pd
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
from werkzeug.utils import secure_filename
from queue import Queue
import threading
from log_manager import LogManager

app = Flask(__name__, template_folder='templates')

# Thư mục lưu trữ
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
LOG_DIR = os.path.join(DATA_DIR, "logs")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# Khởi tạo Log Manager
log_manager = LogManager(LOG_DIR)

# Cấu hình upload
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR

# Queue cho SSE events
event_queue = Queue()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_event(event_type: str, data: dict):
    """Gửi event tới client và lưu log"""
    event_data = {
        'type': event_type,
        **data
    }
    # Lưu log
    log_manager.add_log(event_type, data)
    # Gửi event
    event_queue.put(json.dumps(event_data))

def normalize_conversation(data: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Chuẩn hóa dữ liệu từ Google Sheets thành format JSONL"""
    normalized = []
    for row in data:
        if "user_message" not in row or "assistant_message" not in row:
            continue
            
        user_msg = str(row["user_message"]).strip()
        assistant_msg = str(row["assistant_message"]).strip()
        
        if not user_msg or not assistant_msg or user_msg.lower() == 'nan' or assistant_msg.lower() == 'nan':
            continue
            
        conversation = {
            "messages": [
                {"role": "user", "content": user_msg},
                {"role": "assistant", "content": assistant_msg}
            ]
        }
        normalized.append(conversation)
    return normalized

@app.route('/')
def index():
    # Lấy trạng thái hiện tại của các loại log
    current_states = {
        'webhook': log_manager.get_current_status('webhook'),
        'training': log_manager.get_current_status('training'),
        'upload': log_manager.get_current_status('upload')
    }
    return render_template('index.html', initial_states=current_states)

@app.route('/logs')
def get_logs():
    """API endpoint để lấy logs"""
    log_type = request.args.get('type')
    return jsonify(log_manager.get_logs(log_type))

@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    """API endpoint để xóa logs"""
    log_type = request.json.get('type') if request.json else None
    log_manager.clear_logs(log_type)
    return jsonify({'status': 'success'})

@app.route('/processed-data')
def get_processed_data():
    """API endpoint để lấy dữ liệu đã xử lý gần nhất"""
    return jsonify(log_manager.get_processed_data())

@app.route('/events')
def events():
    """SSE endpoint"""
    def event_stream():
        while True:
            if not event_queue.empty():
                event_data = event_queue.get()
                yield f"data: {event_data}\n\n"
            time.sleep(0.1)
    
    return Response(event_stream(), mimetype='text/event-stream')

def process_data(data: List[Dict[str, Any]], source: str = 'upload') -> tuple:
    """Xử lý dữ liệu và lưu kết quả"""
    try:
        # Chuẩn hóa dữ liệu
        normalized_data = normalize_conversation(data)
        
        if not normalized_data:
            return None, "Không có dữ liệu hợp lệ để xử lý"
            
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        jsonl_path = os.path.join(DATA_DIR, f"training_{timestamp}.jsonl")
        
        # Lưu file JSONL
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for item in normalized_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        # Cập nhật dữ liệu đã xử lý
        processed_data = {
            'raw': data,
            'normalized': normalized_data,
            'file_path': jsonl_path,
            'timestamp': timestamp,
            'source': source,
            'stats': {
                'total_raw': len(data),
                'total_normalized': len(normalized_data),
                'invalid': len(data) - len(normalized_data)
            }
        }
        
        # Lưu vào log manager
        log_manager.update_processed_data(processed_data)
        
        # Gửi event thông báo có dữ liệu mới
        send_event('data', {
            'status': 'Updated',
            'message': 'Đã cập nhật dữ liệu mới',
            'timestamp': timestamp,
            'status_class': 'info'
        })
        
        # Gửi thông báo thành công với stats nếu là webhook
        if source == 'webhook':
            send_event('webhook', {
                'status': 'Success',
                'message': 'Xử lý dữ liệu từ Google Sheets thành công',
                'status_class': 'success',
                'stats': {
                    'total_raw': len(data),
                    'total_normalized': len(normalized_data),
                    'invalid': len(data) - len(normalized_data)
                }
            })
        
        return jsonl_path, None
    except Exception as e:
        return None, str(e)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        send_event('upload', {
            'status': 'error',
            'message': 'Không tìm thấy file',
            'status_class': 'danger'
        })
        return jsonify({'error': 'Không tìm thấy file'}), 400
        
    file = request.files['file']
    if file.filename == '':
        send_event('upload', {
            'status': 'error',
            'message': 'Chưa chọn file',
            'status_class': 'danger'
        })
        return jsonify({'error': 'Chưa chọn file'}), 400
        
    if file and allowed_file(file.filename):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Báo cáo tiến độ upload
            send_event('upload', {
                'status': 'uploading',
                'message': f'Đang tải lên file {filename}',
                'progress': 0,
                'status_class': 'info'
            })
            
            file.save(filepath)
            
            send_event('upload', {
                'status': 'processing',
                'message': 'Đang xử lý file...',
                'progress': 50,
                'status_class': 'warning'
            })
            
            # Đọc file dựa vào định dạng
            if filename.endswith('.csv'):
                df = pd.read_csv(filepath)
            else:  # xlsx
                df = pd.read_excel(filepath)
            
            # Chuyển đổi DataFrame thành list of dicts
            data = df.to_dict('records')
            
            # Xử lý dữ liệu
            jsonl_path, error = process_data(data, 'upload')
            
            if error:
                send_event('upload', {
                    'status': 'error',
                    'message': f'Lỗi: {error}',
                    'status_class': 'danger'
                })
                return jsonify({'error': error}), 500
            
            send_event('upload', {
                'status': 'completed',
                'message': 'Tải lên và xử lý thành công!',
                'progress': 100,
                'status_class': 'success'
            })
            
            # Bắt đầu demo training
            threading.Thread(target=demo_finetune, args=(jsonl_path,)).start()
            
            return jsonify({
                'status': 'success',
                'message': 'Xử lý thành công',
                'file_path': jsonl_path
            })
            
        except Exception as e:
            send_event('upload', {
                'status': 'error',
                'message': f'Lỗi: {str(e)}',
                'status_class': 'danger'
            })
            return jsonify({'error': f'Lỗi xử lý file: {str(e)}'}), 500
            
    send_event('upload', {
        'status': 'error',
        'message': 'Định dạng file không được hỗ trợ',
        'status_class': 'danger'
    })
    return jsonify({'error': 'Định dạng file không được hỗ trợ'}), 400

@app.route('/webhook/sheets', methods=["POST"])
def sheets_webhook():
    try:
        send_event('webhook', {
            'status': 'Processing',
            'message': 'Đang nhận dữ liệu từ Google Sheets...',
            'status_class': 'info'
        })
        
        payload = request.get_json()
        
        if not payload or "data" not in payload:
            send_event('webhook', {
                'status': 'Error',
                'message': 'Không nhận được dữ liệu',
                'status_class': 'danger'
            })
            return jsonify({"error": "Không nhận được dữ liệu"}), 400
            
        sheet_data = payload["data"]
        
        send_event('webhook', {
            'status': 'Normalizing',
            'message': 'Đang chuẩn hóa dữ liệu...',
            'status_class': 'warning'
        })
        
        # Xử lý dữ liệu
        jsonl_path, error = process_data(sheet_data, 'webhook')
        
        if error:
            send_event('webhook', {
                'status': 'Error',
                'message': f'Lỗi: {error}',
                'status_class': 'danger'
            })
            return jsonify({"error": error}), 500
        
        # Demo fine-tune
        threading.Thread(target=demo_finetune, args=(jsonl_path,)).start()
        
        return jsonify({
            "status": "success",
            "message": "Đã xử lý dữ liệu thành công",
            "file_path": jsonl_path
        })
        
    except Exception as e:
        send_event('webhook', {
            'status': 'Error',
            'message': f'Lỗi: {str(e)}',
            'status_class': 'danger'
        })
        return jsonify({"error": str(e)}), 500

def demo_finetune(jsonl_path: str):
    """Demo quá trình fine-tune với LoRA"""
    # Thông báo bắt đầu training
    send_event('training', {
        'status': 'Started',
        'message': 'Bắt đầu quá trình training model...',
        'progress': 0,
        'status_class': 'info'
    })
    steps = [
        ('Initializing', 'Khởi tạo model và tokenizer...'),
        ('Loading', 'Đang tải model Llama-2-7B...'),
        ('Configuring', 'Cấu hình LoRA...'),
        ('Preparing', 'Chuẩn bị training arguments...'),
        ('Training', 'Bắt đầu training...')
    ]
    
    total_steps = len(steps)
    for i, (status, message) in enumerate(steps, 1):
        progress = int((i / total_steps) * 100)
        send_event('training', {
            'status': status,
            'message': message,
            'progress': progress,
            'status_class': 'info'
        })
        time.sleep(1)  # Giả lập thời gian xử lý
    
    # In thông tin training
    print("\n[DEMO] Fine-tuning với LoRA")
    print("=" * 50)
    print(f"""
# 1. Chuẩn bị dữ liệu
training_data = "{jsonl_path}"

# 2. Khởi tạo model và tokenizer
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained(
    "TheBloke/Llama-2-7B-Chat-GGUF",
    device_map="auto",
    trust_remote_code=True
)
tokenizer = AutoTokenizer.from_pretrained("TheBloke/Llama-2-7B-Chat-GGUF")

# 3. Cấu hình LoRA
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=8,                     # Rank của ma trận LoRA
    lora_alpha=32,          # Alpha scaling
    target_modules=["q_proj", "v_proj"],  # Các layer cần fine-tune
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# 4. Áp dụng LoRA
model = get_peft_model(model, lora_config)

# 5. Training arguments
from transformers import TrainingArguments

training_args = TrainingArguments(
    output_dir="./lora_spa_bot",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch"
)

# 6. Khởi tạo Trainer
from transformers import Trainer
import datasets

dataset = datasets.load_dataset("json", data_files=training_data)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset["train"],
)

# 7. Bắt đầu training
# trainer.train()
""")
    print("=" * 50)
    
    send_event('training', {
        'status': 'Completed',
        'message': 'Hoàn thành quá trình xử lý!',
        'progress': 100,
        'status_class': 'success'
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)