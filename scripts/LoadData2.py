import os
import pandas as pd
import pyodbc
import numpy as np
import json
from datetime import datetime
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cấu hình database từ .env
DATABASE_CONFIG = {
    'driver': os.getenv('DB_DRIVER'),
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE'),
    'trusted_connection': os.getenv('DB_TRUSTED_CONNECTION')
}

# Load model từ .env
model_name = os.getenv('EMBEDDING_MODEL')
model = SentenceTransformer(model_name)

# Các bảng cần xử lý
TABLES = ["customers", "customer_tags", "customer_messages", "treatments", "products", "appointments"]

def get_database_connection():
    """Tạo kết nối đến SQL Server"""
    try:
        conn_str = f"""
        DRIVER={{{DATABASE_CONFIG['driver']}}};
        SERVER={DATABASE_CONFIG['server']};
        DATABASE={DATABASE_CONFIG['database']};
        Trusted_Connection={DATABASE_CONFIG['trusted_connection']};
        """
        return pyodbc.connect(conn_str)
    except Exception as e:
        print(f"Lỗi kết nối database: {e}")
        return None

def load_table_from_db(conn, table_name):
    """Load dữ liệu từ bảng với xử lý type conversion"""
    try:
        cursor = conn.cursor()
        cursor.execute(f"""
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """)
        
        columns_info = cursor.fetchall()
        column_selects = []
        
        for col_name, data_type in columns_info:
            if data_type.upper() == 'DATETIMEOFFSET':
                column_selects.append(f"CAST([{col_name}] AS VARCHAR(50)) AS [{col_name}]")
            elif data_type.upper() == 'UNIQUEIDENTIFIER':
                column_selects.append(f"CAST([{col_name}] AS VARCHAR(36)) AS [{col_name}]")
            else:
                column_selects.append(f"[{col_name}]")
        
        query = f"SELECT {', '.join(column_selects)} FROM [{table_name}]"
        return pd.read_sql(query, conn)
        
    except Exception as e:
        print(f"Lỗi load bảng {table_name}: {e}")
        return None

def get_last_update_time():
    """Lấy thời gian cập nhật cuối cùng từ vectordb"""
    try:
        conn = get_database_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        cursor.execute("""
        SELECT MAX(CAST(JSON_VALUE(content, '$.created_at') AS DATETIME2)) 
        FROM document_embeddings
        """)
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
        
    except Exception:
        return None

def get_database_last_modified():
    """Lấy thời gian sửa đổi cuối cùng của các bảng trong database"""
    try:
        conn = get_database_connection()
        if not conn:
            return None
            
        cursor = conn.cursor()
        table_list = "','".join(TABLES)
        cursor.execute(f"""
        SELECT MAX(modify_date) 
        FROM sys.objects 
        WHERE name IN ('{table_list}') AND type = 'U'
        """)
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result and result[0] else None
        
    except Exception:
        return datetime.now()

def create_customer_documents(df, tags_df=None, messages_df=None, treatments_df=None, appointments_df=None):
    """Tạo văn bản tổng hợp thông tin khách hàng"""
    documents = []
    
    # Tạo mapping cho tags
    tag_map = {}
    if tags_df is not None:
        for _, tag_row in tags_df.iterrows():
            tag_map[tag_row['id']] = tag_row['name']
    
    for _, row in df.iterrows():
        customer_id = row['id']
        
        text_lines = [
            "=== THÔNG TIN KHÁCH HÀNG ===",
            f"Tên: {row['name']}",
            f"Giới tính: {row.get('gender', 'không rõ')}",
            f"Điện thoại: {row.get('phone', 'không có')}",
            f"Email: {row.get('email', 'không có')}",
            f"Địa chỉ: {row.get('address', 'không có')}",
            f"Trạng thái: {row.get('status', 'không rõ')}",
            f"Ghi chú: {row['notes'] if pd.notna(row.get('notes')) else 'Không có'}"
        ]
        
        # Thêm thông tin tag
        if pd.notna(row.get('tag_id')) and row['tag_id'] in tag_map:
            text_lines.append(f"Phân loại: {tag_map[row['tag_id']]}")
        
        # Thêm thông tin appointments
        if appointments_df is not None:
            customer_appointments = appointments_df[appointments_df['customer_id'] == customer_id]
            if not customer_appointments.empty:
                text_lines.append(f"\n=== LỊCH HẸN ({len(customer_appointments)} cuộc hẹn) ===")
                for _, apt in customer_appointments.head(3).iterrows():
                    text_lines.append(f"- {apt['appointment_date']} {apt['appointment_time']}: {apt['status']}")
        
        # Thêm thông tin treatments
        if treatments_df is not None:
            customer_treatments = treatments_df[treatments_df['customer_id'] == customer_id]
            if not customer_treatments.empty:
                text_lines.append(f"\n=== LIỆU TRÌNH ({len(customer_treatments)} liệu trình) ===")
                for _, treatment in customer_treatments.head(3).iterrows():
                    text_lines.append(f"- {treatment.get('treatment_name', 'N/A')}: {treatment.get('status', 'N/A')}")
        
        # Thêm thông tin messages
        if messages_df is not None:
            customer_messages = messages_df[messages_df['customer_id'] == customer_id]
            if not customer_messages.empty:
                text_lines.append(f"\n=== TIN NHẮN ({len(customer_messages)} tin nhắn) ===")
                latest_msg = customer_messages.iloc[-1]
                text_lines.append(f"Gần nhất: {latest_msg['message_content'][:100]}...")
        
        documents.append("\n".join(text_lines))
    
    return documents

def create_treatment_documents(df):
    """Tạo văn bản mô tả liệu trình"""
    documents = []
    for _, row in df.iterrows():
        text_lines = [
            "=== LIỆU TRÌNH ===",
            f"Tên: {row.get('treatment_name', 'N/A')}",
            f"Mã: {row.get('id', 'N/A')}",
            f"Tổng buổi: {row.get('total_sessions', 0)}",
            f"Đã thực hiện: {row.get('current_session', 0)}",
            f"Giá: {row.get('price', 0):,} VND",
            f"Trạng thái: {row.get('status', 'N/A')}",
            f"Ghi chú: {row['notes'] if pd.notna(row.get('notes')) else 'Không có'}"
        ]
        documents.append("\n".join(text_lines))
    return documents

def create_product_documents(df):
    """Tạo văn bản mô tả sản phẩm"""
    documents = []
    for _, row in df.iterrows():
        text_lines = [
            "=== SẢN PHẨM ===",
            f"Tên: {row.get('name', 'N/A')}",
            f"Mã: {row.get('id', 'N/A')}",
            f"Trạng thái: {row.get('status', 'N/A')}",
            f"Mô tả: {row['notes'] if pd.notna(row.get('notes')) else 'Chưa có mô tả'}"
        ]
        documents.append("\n".join(text_lines))
    return documents

def load_data_from_database():
    """Load tất cả dữ liệu từ database"""
    conn = get_database_connection()
    if not conn:
        return None
    
    tables_data = {}
    for table_name in TABLES:
        df = load_table_from_db(conn, table_name)
        if df is not None and not df.empty:
            tables_data[table_name] = df
    
    conn.close()
    return tables_data

def create_documents_from_tables(tables_data):
    """Tạo documents từ dữ liệu tables"""
    all_documents = []
    doc_table_map = {}
    
    # Lấy dữ liệu liên quan
    tags_df = tables_data.get('customer_tags')
    messages_df = tables_data.get('customer_messages')
    treatments_df = tables_data.get('treatments')
    appointments_df = tables_data.get('appointments')
    
    # Tạo documents cho customers
    if 'customers' in tables_data:
        docs = create_customer_documents(
            tables_data['customers'], tags_df, messages_df, treatments_df, appointments_df
        )
        start_idx = len(all_documents)
        all_documents.extend(docs)
        for i in range(len(docs)):
            doc_table_map[start_idx + i] = 'customers'
    
    # Tạo documents cho treatments
    if 'treatments' in tables_data:
        docs = create_treatment_documents(tables_data['treatments'])
        start_idx = len(all_documents)
        all_documents.extend(docs)
        for i in range(len(docs)):
            doc_table_map[start_idx + i] = 'treatments'
    
    # Tạo documents cho products
    if 'products' in tables_data:
        docs = create_product_documents(tables_data['products'])
        start_idx = len(all_documents)
        all_documents.extend(docs)
        for i in range(len(docs)):
            doc_table_map[start_idx + i] = 'products'
    
    return all_documents, doc_table_map

def save_embeddings_to_db(documents, embeddings, doc_table_map):
    """Lưu embeddings vào database"""
    conn = get_database_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_embeddings")
        
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            metadata = {
                'doc_id': i,
                'table_name': doc_table_map.get(i, 'unknown'),
                'created_at': datetime.now().isoformat(),
                'vector_dim': len(embedding)
            }
            
            full_content = f"METADATA: {json.dumps(metadata, ensure_ascii=False)}\n\nCONTENT:\n{doc}"
            embedding_json = json.dumps(embedding.tolist())
            
            cursor.execute(
                "INSERT INTO document_embeddings (content, embedding) VALUES (?, ?)",
                (full_content, embedding_json)
            )
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Lỗi lưu embeddings: {e}")
        conn.rollback()
        conn.close()
        return False

def check_and_update_vectordb():
    """Kiểm tra và cập nhật vectordb nếu cần"""
    print("Kiểm tra cập nhật dữ liệu...")
    
    # Lấy thời gian cập nhật cuối của vectordb và database
    last_vector_update = get_last_update_time()
    last_db_modified = get_database_last_modified()
    
    # Kiểm tra xem có cần cập nhật không
    need_update = (
        last_vector_update is None or 
        last_db_modified is None or 
        last_db_modified > last_vector_update
    )
    
    if not need_update:
        print("Dữ liệu đã được cập nhật mới nhất")
        return True
    
    print("Đang cập nhật dữ liệu từ database...")
    
    # Load dữ liệu từ database
    tables_data = load_data_from_database()
    if not tables_data:
        print("Không thể load dữ liệu từ database")
        return False
    
    # Tạo documents
    documents, doc_table_map = create_documents_from_tables(tables_data)
    if not documents:
        print("Không tạo được documents")
        return False
    
    print(f"Tạo embeddings cho {len(documents)} documents...")
    
    # Tạo embeddings
    embeddings = model.encode(documents, show_progress_bar=True)
    
    # Lưu vào database
    success = save_embeddings_to_db(documents, embeddings, doc_table_map)
    
    if success:
        print(f"Cập nhật thành công {len(documents)} documents")
    else:
        print("Lỗi cập nhật dữ liệu")
    
    return success

# Main execution
if __name__ == "__main__":
    check_and_update_vectordb()
