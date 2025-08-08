import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

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