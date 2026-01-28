from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import List, Dict, Optional
from pydantic import BaseModel
from beanie.operators import RegEx
from fastapi.responses import StreamingResponse

from src.agent.graph import chat_with_paper
from src.database import init_database
from src.crawler.scraper import ArxivScraper
from src.utils.log_config import setup_logging, get_logger
from src.processor import VectorProcessor
from src.model import ArxivPaper

logger = None

class CrawlRequest(BaseModel):
    topics: List[str] = []
    keyword: str = ''
    days_back: Optional[int] = 3
    start_date: Optional[str] = None

class SearchRequest(BaseModel):
    keyword: Optional[str] = None
    sort_by: str = "published_date"
    order: str = "desc"
    limit: int = 50

class ChatRequest(BaseModel):
    paper_id: str
    message: str
    history: List[Dict[str, str]] = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    global logger
    logger = get_logger("MainApp")

    logger.info("🚀 The server is starting up...")

    try:
        await init_database()
    except Exception as e:
        logger.critical(f"Failed to initialize the database: {e}")
        raise e
    logger.info("🔄 Activate the Crawler Pipeline to start...")

    try:
        scraper = ArxivScraper()
        processor = VectorProcessor()

        papers = scraper.get_paper(topics=["AI", "CL", "CV", "CL"], days_back=3)
        new_papers = await scraper.save_to_db(papers)

        if new_papers:
            await processor.process_and_index(new_papers)
            logger.info(f"📊 Pipeline complete: {len(new_papers)} new post is ready for chat.")
        else:
            logger.info("⚠️ There are no new posts to process.")
            
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}", exc_info=True)
    logger.info("✅ The system is ready to receive requests!")
    
    yield

    logger.info("🛑 Server is off...")

app = FastAPI(lifespan=lifespan)
@app.get("/")
def read_root():
    return {"status": "running", "service": "Arxiv Agent"}

@app.get("/news/latest")
async def get_latest_news():
    papers = await ArxivPaper.find_all().sort("-published_date").limit(20).to_list()
    return papers

@app.post("/crawler/trigger")
async def trigger_craw(request: CrawlRequest):
    """
    API for Frontend to immediately issue commands to scrape data. 
    """
    logger.info(f'Receive commands to manually retrieve news: {request.topics} within {request.days_back} days.')
    try:
        scraper = ArxivScraper()
        processor = VectorProcessor()

        papers = scraper.get_paper(
            topics=request.topics,
            keyword=request.keyword,
            days_back=request.days_back,
            start_date=request.start_date
        )
        new_papers = await scraper.save_to_db(papers)

        if new_papers:
            await processor.process_and_index(new_papers)
            return {
                "status": "success", 
                "message": f"{len(new_papers)} new articles were found and processed", 
                "count": len(new_papers)
            }
        else:
            return {
                "status": "success", 
                "message": "Đã chạy xong nhưng không có bài báo mới (hoặc đã tồn tại trong DB).",
                "count": 0
            }
    except Exception as e:
        logger.error(f"❌ Crawl error: {e}", exc_info=True)
        return {"status": "error", "message": str(e)}
    
@app.post('/papers/search')
async def search_papers(request: SearchRequest):
    """
    API retrieves a list of articles from Mongo with sorting.
    """
    sort_prefix = "-" if request.order == "desc" else "+"
    valid_fields = ["published_date", "updated_date", "crawled_at"]
    field = request.sort_by if request.sort_by in valid_fields else "published_date"
    sort_str = f"{sort_prefix}{field}"
    
    if request.keyword and request.keyword.strip():
        search_pattern = request.keyword.strip()
        query = ArxivPaper.find({
            "title": {"$regex": search_pattern, "$options": "i"}
        })
    else:
        query = ArxivPaper.find_all()
        
    papers = await query.sort(sort_str).limit(request.limit).to_list()
    
    logger.info(f"🔍 Search: Key='{request.keyword}' | Found: {len(papers)}")
    return papers

from fastapi.responses import StreamingResponse
import asyncio

@app.post("/chat/stream")
async def chat_stream(body: ChatRequest):
    """
    API Chat Streaming với Gemini
    """
    logger.info(f"💬 Chat request for paper {body.paper_id}: {body.message[:50]}...")
    async def response_generator():
        async for chunk in chat_with_paper(body.paper_id, body.message, body.history):
            yield chunk
            
    return StreamingResponse(response_generator(), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run('src.main:app', host='0.0.0.0', port=8000, reload=True)