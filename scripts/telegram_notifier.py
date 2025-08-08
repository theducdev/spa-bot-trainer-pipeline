import os
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class TelegramNotifier:
    def __init__(self):
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message: str, parse_mode: Optional[str] = 'HTML') -> bool:
        """
        Gửi tin nhắn qua Telegram
        Args:
            message: Nội dung tin nhắn
            parse_mode: HTML hoặc Markdown
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        if not self.bot_token or not self.chat_id:
            print("Telegram credentials not configured")
            return False

        try:
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            response = requests.post(self.api_url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")
            return False

# Khởi tạo instance để sử dụng trong toàn bộ ứng dụng
notifier = TelegramNotifier()