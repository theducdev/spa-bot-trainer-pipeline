from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import pyodbc
import json
from sklearn.metrics.pairwise import cosine_similarity
from underthesea import ner , pos_tag 
from itertools import groupby
import re 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cấu hình database từ environment variables
DATABASE_CONFIG = {
    'driver': os.getenv('DB_DRIVER'),
    'server': os.getenv('DB_SERVER'),
    'database': os.getenv('DB_DATABASE'),
    'trusted_connection': os.getenv('DB_TRUSTED_CONNECTION')
}

# Load model từ environment variable
model_name = os.getenv('EMBEDDING_MODEL')
embedding_model = SentenceTransformer(model_name)


# Cache cho documents từ database
_documents_cache = None
_embeddings_cache = None
_doc_table_map_cache = None

def get_database_connection():
    """Tạo kết nối đến SQL Server"""
    try:
        if 'username' in DATABASE_CONFIG and 'password' in DATABASE_CONFIG:
            conn_str = f"""
            DRIVER={{{DATABASE_CONFIG['driver']}}};
            SERVER={DATABASE_CONFIG['server']};
            DATABASE={DATABASE_CONFIG['database']};
            UID={DATABASE_CONFIG['username']};
            PWD={DATABASE_CONFIG['password']};
            """
        else:
            conn_str = f"""
            DRIVER={{{DATABASE_CONFIG['driver']}}};
            SERVER={DATABASE_CONFIG['server']};
            DATABASE={DATABASE_CONFIG['database']};
            Trusted_Connection={DATABASE_CONFIG['trusted_connection']};
            """
        
        conn = pyodbc.connect(conn_str)
        return conn
    except Exception as e:
        print(f"❌ Lỗi kết nối database: {e}")
        return None

def load_documents_from_db():
    """Load documents và embeddings từ database với cache"""
    global _documents_cache, _embeddings_cache, _doc_table_map_cache
    
    # Nếu đã có cache, trả về luôn
    if _documents_cache is not None:
        return _documents_cache, _embeddings_cache, _doc_table_map_cache
    
    conn = get_database_connection()
    if not conn:
        return {}, [], {}
    
    try:
        query = "SELECT id, content, embedding FROM document_embeddings ORDER BY id"
        df = pd.read_sql(query, conn)
        
        doc_map = {}
        embeddings = []
        doc_table_map = {}
        
        for idx, row in df.iterrows():
            doc_id = row['id']
            content = row['content']
            
            # Parse embedding từ JSON
            embedding = np.array(json.loads(row['embedding']))
            embeddings.append(embedding)
            
            # Parse content và metadata
            if content.startswith('METADATA:'):
                try:
                    parts = content.split('\n\nCONTENT:\n', 1)
                    if len(parts) == 2:
                        metadata_str = parts[0].replace('METADATA: ', '')
                        metadata = json.loads(metadata_str)
                        
                        actual_content = parts[1]
                        table_name = metadata.get('table_name', 'unknown')
                        original_doc_id = metadata.get('doc_id', doc_id)
                        
                        doc_map[original_doc_id] = actual_content
                        doc_table_map[original_doc_id] = table_name
                    else:
                        doc_map[doc_id] = content
                        doc_table_map[doc_id] = 'unknown'
                except:
                    doc_map[doc_id] = content
                    doc_table_map[doc_id] = 'unknown'
            else:
                doc_map[doc_id] = content
                doc_table_map[doc_id] = 'unknown'
        
        # Cache kết quả
        _documents_cache = doc_map
        _embeddings_cache = np.array(embeddings) if embeddings else np.array([])
        _doc_table_map_cache = doc_table_map
        
        conn.close()
        print(f"✅ Đã load {len(doc_map)} documents từ database")
        return doc_map, _embeddings_cache, doc_table_map
        
    except Exception as e:
        print(f"❌ Lỗi load documents từ database: {e}")
        conn.close()
        return {}, [], {}

# Load documents khi khởi tạo module
doc_map, embeddings_matrix, doc_table_map = load_documents_from_db()

def refresh_cache():
    """Làm mới cache từ database"""
    global _documents_cache, _embeddings_cache, _doc_table_map_cache, doc_map, embeddings_matrix, doc_table_map
    
    _documents_cache = None
    _embeddings_cache = None
    _doc_table_map_cache = None
    
    doc_map, embeddings_matrix, doc_table_map = load_documents_from_db()
    print("🔄 Đã làm mới cache từ database")

def get_database_stats():
    """Lấy thống kê về database"""
    conn = get_database_connection()
    if not conn:
        return "❌ Không thể kết nối database"
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM document_embeddings")
        count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT JSON_VALUE(content, '$.table_name')) FROM document_embeddings WHERE content LIKE 'METADATA:%'")
        table_count = cursor.fetchone()[0]
        
        conn.close()
        return f"📊 Database có {count} documents từ {table_count} bảng khác nhau"
    
    except Exception as e:
        conn.close()
        return f"❌ Lỗi lấy thống kê database: {e}"






def search_exact_customer(customer_name):

    # Chuẩn hóa tên tìm kiếm
    customer_name = customer_name.strip().lower()
    
    found_customers = []
    
    # Tìm trong tất cả documents
    for doc_id, content in doc_map.items():
        # Chỉ tìm trong documents của bảng customers
        table_name = doc_table_map.get(doc_id, '')
        if table_name == 'customers':
            content_lower = content.lower()
            
            # 1. "khách hàng: tên"
            if f"khách hàng: {customer_name}" in content_lower:
                found_customers.append(content)
            # 2. "tên khách hàng: tên"  
            elif f"tên khách hàng: {customer_name}" in content_lower:
                found_customers.append(content)
            # 3. "họ tên: tên"
            elif f"họ tên: {customer_name}" in content_lower:
                found_customers.append(content)
            # 4. "name: tên"
            elif f"name: {customer_name}" in content_lower:
                found_customers.append(content)
            # 5. "tên: tên"
            elif f"tên: {customer_name}" in content_lower:
                found_customers.append(content)
            # 6. "fullname: tên"
            elif f"fullname: {customer_name}" in content_lower:
                found_customers.append(content)
            # 7. Tìm tên trong bất kỳ đâu trong content (loose matching)
            elif customer_name in content_lower:
                found_customers.append(content)
    
    if found_customers:
        if len(found_customers) == 1:
            return found_customers[0]
        else:
            # Trả về tất cả khách hàng cùng tên
            result = f"Tìm thấy {len(found_customers)} khách hàng có tên '{customer_name}':\n\n"
            for i, customer in enumerate(found_customers, 1):
                result += f"=== KHÁCH HÀNG {i} ===\n{customer}\n\n"
            return result.strip()
    
    return None

def search_customer_by_phone(phone):

    phone_clean = re.sub(r'[\s\-\(\)\+]', '', phone.strip())
    
    phone_variants = [phone_clean]
    
    # Nếu bắt đầu bằng 84, thêm biến thể với 0
    if phone_clean.startswith('84') and len(phone_clean) == 11:
        phone_variants.append('0' + phone_clean[2:])
    
    # Nếu bắt đầu bằng 0, thêm biến thể với 84
    if phone_clean.startswith('0') and len(phone_clean) == 10:
        phone_variants.append('84' + phone_clean[1:])
    
    # Tìm trong tất cả documents
    for doc_id, content in doc_map.items():
        # Chỉ tìm trong documents của bảng customers
        table_name = doc_table_map.get(doc_id, '')
        if table_name == 'customers':
            # Tìm số điện thoại trong nội dung (loại bỏ ký tự đặc biệt khi so sánh)
            content_clean = re.sub(r'[\s\-\(\)\+]', '', content)
            
            # Kiểm tra tất cả các biến thể
            for variant in phone_variants:
                if variant in content_clean:
                    return content
    
    return None

def search_customer_by_email(email):

    email = email.strip().lower()
    
    for doc_id, content in doc_map.items():
        # Chỉ tìm trong documents của bảng customers
        table_name = doc_table_map.get(doc_id, '')
        if table_name == 'customers':
            # Kiểm tra nếu email có trong nội dung
            if email in content.lower():
                return content
    
    return None




def search_customer_comprehensive(query):
    """
    Tìm kiếm khách hàng toàn diện theo tên, số điện thoại hoặc email
    
    Args:
        query (str): Truy vấn tìm kiếm (có thể chứa tên, số điện thoại hoặc email)
        
    Returns:
        dict: Kết quả tìm kiếm với thông tin về phương thức tìm thấy
    """
    # Thử các phương thức tìm kiếm theo thứ tự ưu tiên
    
    # 1. Tìm kiếm theo email
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    email_matches = re.findall(email_pattern, query)
    if email_matches:
        for email in email_matches:
            result = search_customer_by_email(email)
            if result:
                return {
                    'found': True,
                    'method': 'email',
                    'search_term': email,
                    'content': result
                }
    
    # 2. Tìm kiếm theo số điện thoại
    phone_patterns = [
        r'\b0\d{9}\b',  # Số điện thoại Việt Nam bắt đầu bằng 0 (10 số)
        r'\b\+84\d{9}\b',  # Số điện thoại quốc tế với +84
        r'\b84\d{9}\b',  # Số điện thoại quốc tế không có dấu +
        r'\b0\d{2}[\s\-]?\d{3}[\s\-]?\d{4}\b',  # Số có dấu phân cách dạng 0xx-xxx-xxxx
        r'\b0\d{3}[\s\-]?\d{3}[\s\-]?\d{3}\b',   # Số có dấu phân cách dạng 0xxx-xxx-xxx
        r'\b\d{10}\b',  # Bất kỳ dãy 10 số nào (có thể là số điện thoại)
        r'\b\d{11}\b'   # Bất kỳ dãy 11 số nào (có thể là số điện thoại quốc tế)
    ]
    
    for pattern in phone_patterns:
        phone_matches = re.findall(pattern, query)
        if phone_matches:
            for phone in phone_matches:
                result = search_customer_by_phone(phone)
                if result:
                    return {
                        'found': True,
                        'method': 'phone',
                        'search_term': phone,
                        'content': result
                    }
    
    # 3. Tìm kiếm theo tên
    name_patterns = [
        r'thông tin khách hàng[:\s]+([^,\n]+)',
        r'khách hàng[:\s]+([^,\n]+)',
        r'tìm.*?([A-ZĐÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZĐÀ-Ỹ][a-zà-ỹ]+)*)',
        r'([A-ZĐÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZĐÀ-Ỹ][a-zà-ỹ]+)+)'
    ]
    
    for pattern in name_patterns:
        matches = re.findall(pattern, query)
        if matches:
            customer_name = matches[0].strip()
            result = search_exact_customer(customer_name)
            if result:
                return {
                    'found': True,
                    'method': 'name',
                    'search_term': customer_name,
                    'content': result
                }
    
    return {
        'found': False,
        'method': None,
        'search_term': None,
        'content': None
    }

def retrieve_top_k(query, k):
    """
    Tìm kiếm thông tin với quy trình 2 bước:
    1. Tìm kiếm keyword trước (exact search cho khách hàng)
    2. Dùng kết quả keyword để làm semantic search, hoặc semantic search trực tiếp nếu không có keyword
    """
    global embeddings_matrix, doc_map
    
    if len(embeddings_matrix) == 0:
        return "❌ Không có dữ liệu embedding trong database. Vui lòng chạy LoadData.py trước."
    
    #Thử tìm kiếm chính xác khách hàng trước (keyword search)
    search_result = search_customer_comprehensive(query)
    
    # Nếu tìm thấy kết quả keyword, dùng nó làm cơ sở cho semantic search
    if search_result['found']:
        method_name = {
            'email': 'email',
            'phone': 'số điện thoại', 
            'name': 'tên'
        }
        
        keyword_content = search_result['content']
        
        #  Dùng kết quả keyword để làm semantic search
        # Tạo embedding cho keyword result và query kết hợp
        combined_query = f"{query} {keyword_content}"
        query_embedding = embedding_model.encode([combined_query], convert_to_numpy=True)
        
        # Tính cosine similarity với tất cả embeddings
        similarities = cosine_similarity(query_embedding, embeddings_matrix)[0]
        
        # Lấy top k indices có similarity cao nhất
        top_indices = np.argsort(similarities)[::-1][:k]
        
        # Lấy văn bản tương ứng
        results = []
        
        # Luôn bao gồm kết quả keyword đầu tiên
        # results.append(f"🎯 Tìm thấy khách hàng theo {method_name[search_result['method']]}: {search_result['search_term']}\n{keyword_content}")
        
        # Thêm các kết quả semantic liên quan (loại bỏ trùng lặp với keyword result)
        for idx in top_indices[:k-1]:  # Lấy k-1 vì đã có 1 kết quả keyword
            if idx in doc_map and similarities[idx] > 0.1:
                content = doc_map[idx]
                # Kiểm tra không trùng với kết quả keyword
                if content != keyword_content:
                    similarity_score = similarities[idx]
                    results.append(f"📊 Độ tương đồng: {similarity_score:.3f}\n{content}")
        
        return '🔍 Kết quả tìm kiếm kết hợp (Keyword + Semantic):\n\n' + '\n\n---\n\n'.join(results)
    
    # Nếu không tìm thấy keyword, dùng semantic search trực tiếp
    # Tạo embedding cho query
    query_embedding = embedding_model.encode([query], convert_to_numpy=True)
    
    # Tính cosine similarity với tất cả embeddings
    similarities = cosine_similarity(query_embedding, embeddings_matrix)[0]
    
    # Lấy top k indices có similarity cao nhất
    top_indices = np.argsort(similarities)[::-1][:k]
    
    # Kiểm tra nếu không tìm thấy kết quả nào có similarity đủ cao
    if len(top_indices) == 0 or similarities[top_indices[0]] < 0.1:
        return "❌ Không tìm thấy thông tin phù hợp. Vui lòng kiểm tra lại tên khách hàng, số điện thoại, email hoặc thử với từ khóa khác."
    
    # Lấy văn bản tương ứng
    results = []
    for idx in top_indices:
        if idx in doc_map and similarities[idx] > 0.1:  # Chỉ lấy những kết quả có similarity > 0.1
            similarity_score = similarities[idx]
            content = doc_map[idx]
            results.append(f"📊 Độ tương đồng: {similarity_score:.3f}\n{content}")
    
    if not results:
        return "❌ Không tìm thấy thông tin phù hợp. Vui lòng kiểm tra lại tên khách hàng, số điện thoại, email hoặc thử với từ khóa khác."
    
    return '🔍 Kết quả tìm kiếm ngữ nghĩa từ database:\n\n' + '\n\n---\n\n'.join(results)







