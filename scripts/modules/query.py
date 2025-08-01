import google.generativeai as genai
from modules.retrived_rag import retrieve_top_k
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Query(object):

    def __init__(self, query):
        self.text = query
        # # Cấu hình Gemini API từ environment variable
        # api_key = os.getenv('GEMINI_API_KEY')
        # if not api_key:
        #     raise ValueError("GEMINI_API_KEY không tìm thấy trong file .env")
        
        # genai.configure(api_key=api_key)
        # self.model = genai.GenerativeModel('gemini-1.5-flash')

    def process_RAG(self):
        retrieved_texts = retrieve_top_k(self.text, k=3)


        # phần xử lý văn bản đã lấy bằng LLM

        return retrieved_texts
 