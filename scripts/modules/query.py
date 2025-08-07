import google.generativeai as genai
from modules.retrived_rag import retrieve_top_k
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Query(object):

    def __init__(self, query):
        self.text = query
        # Cấu hình Ollama
        self.ollama_url = os.getenv('OLLAMA_URL' )
        self.model_name = os.getenv('OLLAMA_MODEL')

    def generate_response_with_gemini(self, context, query):
        """Sinh câu trả lời bằng Gemini API"""
        # Cấu hình Gemini
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            return "❌ Chưa cấu hình GEMINI_API_KEY trong file .env"
        
        genai.configure(api_key=api_key)
        
        prompt = f"""Bạn là trợ lý ảo của spa chuyên nghiệp để hỗ trợ nhân viên tìm kiếm thông tin khách hàng. Hãy phân tích thông tin được cung cấp và trả lời câu hỏi của nhân viên một cách chính xác, hữu ích và tập trung.

Quy tắc trả lời:
- Chỉ sử dụng thông tin có trong dữ liệu được cung cấp
- Nếu nhân viên hỏi về liệu trình, chỉ tập trung vào thông tin có prefix "[Liệu trình]"
- Nếu hỏi về thông tin cá nhân, chỉ sử dụng thông tin trong "=== THÔNG TIN KHÁCH HÀNG ==="
- Trả lời ngắn gọn, rõ ràng và thân thiện
- Nếu không tìm thấy thông tin phù hợp, hãy thông báo lịch sự

Thông tin tham khảo:
{context}

Câu hỏi của nhân viên: {query}

Trả lời:"""

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"❌ Lỗi Gemini API: {e}")
            return context

    def generate_response_with_ollama(self, context, query):
        """Sinh câu trả lời bằng Ollama"""
        prompt = f"""Bạn là trợ lý ảo của spa để hỗ trợ nhân viên. Dựa vào thông tin sau đây, hãy trả lời câu hỏi của nhân viên một cách chính xác và hữu ích.

        Thông tin tham khảo:
        {context}

        Câu hỏi: {query}

        Trả lời:"""

        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=300
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                return context
                
        except requests.exceptions.Timeout:
            return context
        except Exception as e:
            return context

    def process_RAG(self):
        retrieved_texts = retrieve_top_k(self.text, k=4)
        
        # Sinh câu trả lời bằng Gemini API
        # response = self.generate_response_with_gemini(retrieved_texts, self.text)
        
        # Sử dụng Ollama chạy model local
        response = self.generate_response_with_ollama(retrieved_texts, self.text)
        
        return response, retrieved_texts
 