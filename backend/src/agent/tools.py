from datetime import datetime, timezone
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.document_loaders import PyMuPDFLoader

from src.model import ArxivPaper
from src.utils.log_config import get_logger
from src.agent.paper_processor import summarize_and_analyze_pdf

logger = get_logger("AgentTools")

@tool
def web_search(query: str):
    """
    Sử dụng công cụ này khi cần tìm kiếm các thông tin, kiến thức bên ngoài (General Knowledge),
    các khái niệm mới, hoặc thông tin cập nhật không có trong bài báo.
    """
    logger.info(f"🔎 Agent đang search web: {query}")
    search = DuckDuckGoSearchRun()
    return search.run(query)

@tool
async def read_full_paper(paper_id: str):
    """
    Sử dụng công cụ này khi người dùng hỏi chi tiết sâu về bài báo (Methodology, Experiment, Math).
    Công cụ này sẽ TẢI PDF -> PHÂN TÍCH -> TRẢ VỀ bản phân tích chi tiết.
    """
    logger.info(f"📥 Agent phân tích: {paper_id}")
    
    paper = await ArxivPaper.get(paper_id)
    if not paper:
        return "Không tìm thấy bài báo trong Database."

    if hasattr(paper, "deep_analysis") and paper.deep_analysis:
        logger.info("✅ Đã có bản phân tích trong Cache. Lấy ra dùng ngay.")
        return paper.deep_analysis

    try:
        pdf_url = paper.pdf_url or f"http://arxiv.org/pdf/{paper.id}.pdf"
            
        logger.info(f"Downloading PDF from: {pdf_url}")
        
        loader = PyMuPDFLoader(pdf_url)
        docs = loader.load()
        raw_full_text = "\n\n".join([doc.page_content for doc in docs])
        analysis_text = await summarize_and_analyze_pdf(raw_full_text)

        paper.deep_analysis = analysis_text
        paper.analyzed_at = datetime.now(timezone.utc)
        await paper.save()
        
        logger.info("✅ Đã lưu bản phân tích vào DB.")
        return analysis_text
        
    except Exception as e:
        logger.error(f"Lỗi quy trình đọc PDF: {e}")
        return f"Không thể đọc bài báo: {str(e)}"