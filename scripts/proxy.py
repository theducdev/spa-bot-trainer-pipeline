import os
import re
import requests
import mysql.connector
from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv()

app = Flask(__name__)

# Kết nối database
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME")
    )

# Route chính
@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    prompt = data.get("prompt", "")
    enriched_prompt = prompt

    # Tìm mã khách hàng dạng KH123
    match = re.search(r"KH\d+", prompt)
    if match:
        customer_id = match.group(0)
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM customers WHERE id = %s", (customer_id,))
            customer = cursor.fetchone()

            if customer:
                enriched_prompt = (
                    f"Thông tin khách hàng: tên {customer['name']}, "
                    f"dịch vụ gần nhất: {customer['last_service']}. "
                    f"Câu hỏi: {prompt}"
                )
        except Exception as e:
            print(f"Lỗi truy vấn DB: {e}")
        finally:
            cursor.close()
            conn.close()

    # Gửi prompt đến Ollama
    try:
        response = requests.post(
            os.getenv("OLLAMA_API"),
            json={"model": "spa-bot", "prompt": enriched_prompt, "stream": False}
        )
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        print(f"Lỗi gọi Ollama: {e}")
        return jsonify({"error": "Lỗi gửi prompt đến Ollama"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
