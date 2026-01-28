import os
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.agents import create_agent

from src.model import ArxivPaper
from src.utils.log_config import get_logger
from src.agent.tools import web_search, read_full_paper

logger = get_logger("AgentGraph")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-lite", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0.5,
    streaming=True
)

tools = [web_search, read_full_paper]

SYSTEM_PROMPT = """Bạn là một Trợ lý Nghiên cứu AI (AI Research Assistant) cao cấp.
Bạn đang hỗ trợ người dùng tìm hiểu về một bài báo khoa học cụ thể.

QUY TRÌNH SUY LUẬN:
1. Đọc câu hỏi của người dùng.
2. Kiểm tra xem thông tin có trong phần "TÓM TẮT BÀI BÁO" (Abstract) đã được cung cấp sẵn hay không.
3. Nếu câu hỏi về kiến thức chung (ví dụ: "Transformer là gì?", "YOLO ra đời năm nào?"), hãy dùng công cụ `web_search`.
4. Nếu câu hỏi yêu cầu chi tiết SÂU trong bài báo (ví dụ: "Công thức loss function là gì?", "Kết quả bảng 3 thế nào?"), hãy dùng công cụ `read_full_paper` với ID bài báo.
5. Sau khi có thông tin từ tool, hãy tổng hợp và trả lời bằng Tiếng Việt chuyên nghiệp.

Lưu ý:
- KHÔNG gọi tool `read_full_paper` nếu chỉ hỏi tóm tắt hoặc thông tin cơ bản.
- Khi gọi `read_full_paper`, hãy kiên nhẫn đọc nội dung trả về.
"""

agent_executor = create_agent(llm, tools, system_prompt=SYSTEM_PROMPT)

async def chat_with_paper(paper_id: str, user_query: str, history: list) -> Any:
    """
    Hàm entrypoint để gọi Agent.
    """
    paper = await ArxivPaper.get(paper_id)
    if not paper:
        yield "Xin lỗi, tôi không tìm thấy thông tin bài báo này trong cơ sở dữ liệu."
        return

    context_msg = f"""
    --- CONTEXT BÀI BÁO ĐANG THẢO LUẬN ---
    ID: {paper.id}
    Title: {paper.title}
    Abstract: {paper.summary}
    ---------------------------------------
    """

    langchain_history = [SystemMessage(content=context_msg)]
    for msg in history:
        if msg['role'] == 'user':
            langchain_history.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            langchain_history.append(AIMessage(content=msg['content']))
    
    langchain_history.append(HumanMessage(content=user_query))

    try:
        async for event in agent_executor.astream_events(
            {"messages": langchain_history},
            version="v1"
        ):
            kind = event["event"]
            if kind == "on_tool_start":
                tool_name = event['name']
                if tool_name == "web_search":
                    yield f"\n\n*🔍 Đang tìm kiếm thông tin trên web...*\n\n"
                elif tool_name == "read_full_paper":
                    yield f"\n\n*📥 Đang tải và đọc toàn văn bài báo (Full PDF)...*\n\n"

            elif kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content

    except Exception as e:
        logger.error(f"Lỗi Agent: {e}", exc_info=True)
        yield f"\n\n[Lỗi hệ thống: {str(e)}]"