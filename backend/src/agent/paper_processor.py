import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.utils.log_config import get_logger

logger = get_logger("PaperProcessor")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.2
)

ANALYSIS_PROMPT = """Bạn là một Chuyên gia phân tích bài báo khoa học (AI Researcher).
Nhiệm vụ của bạn là đọc toàn văn nội dung thô của một bài báo và tạo ra bản "PHÂN TÍCH CHUYÊN SÂU" (Deep Analysis).

Mục tiêu: Bản phân tích này sẽ được dùng để lưu trữ và trả lời câu hỏi sau này, nên nó phải chi tiết các ý chính nhưng ngắn gọn hơn văn bản gốc.

Vui lòng trích xuất và trình bày theo cấu trúc Markdown sau:

# 1. Đóng góp cốt lõi (Core Contributions)
- Liệt kê các điểm mới/đóng góp quan trọng nhất của bài báo.

# 2. Phương pháp luận (Methodology)
- Mô tả chi tiết kiến trúc/thuật toán đề xuất.
- Cách họ giải quyết vấn đề (Input -> Process -> Output).
- Các công thức toán học hoặc hàm loss quan trọng (mô tả bằng lời hoặc LaTeX đơn giản).

# 3. Thực nghiệm & Kết quả (Experiments & Results)
- Dataset sử dụng.
- Metric đánh giá.
- Các bảng/biểu đồ quan trọng nói lên điều gì?

# 4. Hạn chế & Hướng phát triển (Limitations & Future Work)
- Tác giả tự nhận khuyết điểm gì?

--- NỘI DUNG VĂN BẢN GỐC ---
{full_text}
"""

async def summarize_and_analyze_pdf(raw_text: str) -> str:
    """
    Hàm nhận text thô -> Gọi LLM phân tích -> Trả về Markdown Analysis
    """
    try:
        logger.info("🧠 Đang gọi LLM để phân tích sâu nội dung PDF...")
        
        prompt = ChatPromptTemplate.from_template(ANALYSIS_PROMPT)
        chain = prompt | llm | StrOutputParser()
        
        analysis_result = await chain.ainvoke({"full_text": raw_text})
        
        logger.info("✅ Phân tích hoàn tất.")
        return analysis_result
        
    except Exception as e:
        logger.error(f"Lỗi khi phân tích bài báo: {e}")
        return f"⚠️ Lỗi phân tích AI. Dưới đây là trích đoạn đầu:\n\n{raw_text[:5000]}..."