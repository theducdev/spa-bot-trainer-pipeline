import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram_notifier import notifier

class LogManager:
    def __init__(self, log_dir: str):
        """Khởi tạo LogManager với thư mục lưu logs"""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # File paths cho từng loại log
        self.log_files = {
            'webhook': os.path.join(log_dir, 'webhook_logs.json'),
            'training': os.path.join(log_dir, 'training_logs.json'),
            'upload': os.path.join(log_dir, 'upload_logs.json')
        }
        
        # File path cho processed data
        self.processed_data_file = os.path.join(log_dir, 'processed_data.json')
        
        # Khởi tạo file logs nếu chưa tồn tại
        for log_file in self.log_files.values():
            if not os.path.exists(log_file):
                with open(log_file, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False)
                    
        # Khởi tạo file processed data nếu chưa tồn tại
        if not os.path.exists(self.processed_data_file):
            self._write_processed_data({
                'raw': None,
                'normalized': None,
                'file_path': None,
                'timestamp': None,
                'source': None,
                'stats': None
            })

    def add_log(self, log_type: str, data: Dict[str, Any]) -> None:
        """Thêm một log mới"""
        if log_type not in self.log_files:
            return
            
        # Thêm timestamp vào log
        log_entry = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            **data
        }
        
        # Đọc logs hiện tại
        logs = self._read_logs(log_type)
        logs.append(log_entry)
        
        # Lưu logs
        self._write_logs(log_type, logs)
        
        # Cập nhật trạng thái hiện tại
        self._update_current_status(log_type, data)
        
        # Gửi thông báo Telegram cho webhook và training
        if log_type in ['webhook', 'training']:
            self._send_telegram_notification(log_type, data)

    def get_logs(self, log_type: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Lấy tất cả logs hoặc logs của một loại cụ thể"""
        if log_type:
            if log_type not in self.log_files:
                return []
            return self._read_logs(log_type)
            
        # Trả về tất cả logs
        return {
            log_type: self._read_logs(log_type)
            for log_type in self.log_files.keys()
        }

    def clear_logs(self, log_type: Optional[str] = None) -> None:
        """Xóa logs"""
        if log_type:
            if log_type in self.log_files:
                self._write_logs(log_type, [])
                # Reset status
                self._update_current_status(log_type, {
                    'status': 'Not Started',
                    'message': 'Chưa có hoạt động',
                    'status_class': 'secondary',
                    'progress': 0
                })
        else:
            # Xóa tất cả logs
            for log_type in self.log_files:
                self._write_logs(log_type, [])
                self._update_current_status(log_type, {
                    'status': 'Not Started',
                    'message': 'Chưa có hoạt động',
                    'status_class': 'secondary',
                    'progress': 0
                })

    def get_current_status(self, log_type: str) -> Dict[str, Any]:
        """Lấy trạng thái hiện tại của một loại log"""
        status_file = os.path.join(self.log_dir, f'{log_type}_status.json')
        
        if not os.path.exists(status_file):
            return {
                'status': 'Not Started',
                'message': 'Chưa có hoạt động',
                'status_class': 'secondary',
                'progress': 0
            }
            
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'status': 'Not Started',
                'message': 'Chưa có hoạt động',
                'status_class': 'secondary',
                'progress': 0
            }

    def update_processed_data(self, data: Dict[str, Any]) -> None:
        """Cập nhật dữ liệu đã xử lý"""
        self._write_processed_data(data)

    def get_processed_data(self) -> Dict[str, Any]:
        """Lấy dữ liệu đã xử lý gần nhất"""
        try:
            with open(self.processed_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'raw': None,
                'normalized': None,
                'file_path': None,
                'timestamp': None,
                'source': None,
                'stats': None
            }

    def _read_logs(self, log_type: str) -> List[Dict[str, Any]]:
        """Đọc logs từ file"""
        try:
            with open(self.log_files[log_type], 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def _write_logs(self, log_type: str, logs: List[Dict[str, Any]]) -> None:
        """Ghi logs vào file"""
        with open(self.log_files[log_type], 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def _update_current_status(self, log_type: str, status: Dict[str, Any]) -> None:
        """Cập nhật trạng thái hiện tại"""
        status_file = os.path.join(self.log_dir, f'{log_type}_status.json')
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(status, f, ensure_ascii=False, indent=2)

    def _write_processed_data(self, data: Dict[str, Any]) -> None:
        """Ghi dữ liệu đã xử lý vào file"""
        with open(self.processed_data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def _send_telegram_notification(self, log_type: str, data: Dict[str, Any]) -> None:
        """Gửi thông báo qua Telegram dựa trên loại log và dữ liệu"""
        if log_type == 'webhook':
            if data.get('status') == 'Success':
                stats = data.get('stats', {})
                message = (
                    "🔔 <b>Webhook Update</b>\n\n"
                    f"✅ Nhận dữ liệu mới từ Google Sheets\n"
                    f"📊 Thống kê:\n"
                    f"- Tổng số mẫu: {stats.get('total_raw', 0)}\n"
                    f"- Mẫu hợp lệ: {stats.get('total_normalized', 0)}\n"
                    f"- Mẫu không hợp lệ: {stats.get('invalid', 0)}\n\n"
                    f"💬 Chi tiết: {data.get('message', '')}"
                )
                notifier.send_message(message)
            elif data.get('status') == 'Error':
                message = (
                    "🔔 <b>Webhook Error</b>\n\n"
                    f"❌ {data.get('message', 'Có lỗi xảy ra trong quá trình xử lý webhook')}"
                )
                notifier.send_message(message)

        elif log_type == 'training':
            status = data.get('status', '')
            if status == 'Started':
                message = (
                    "🔔 <b>Training Started</b>\n\n"
                    "🚀 Bắt đầu quá trình training model..."
                )
                notifier.send_message(message)
            elif status == 'Completed':
                message = (
                    "🔔 <b>Training Completed</b>\n\n"
                    "✅ Quá trình training đã hoàn thành thành công!"
                )
                notifier.send_message(message)
            elif status == 'Error':
                message = (
                    "🔔 <b>Training Error</b>\n\n"
                    f"❌ {data.get('message', 'Có lỗi xảy ra trong quá trình training')}"
                )
                notifier.send_message(message)
            elif 'progress' in data:
                progress = data.get('progress', 0)
                if progress > 0 and progress % 25 == 0:  # Thông báo mỗi 25%
                    message = (
                        "🔔 <b>Training Progress</b>\n\n"
                        f"📊 Tiến độ: {progress}%"
                    )
                    notifier.send_message(message)