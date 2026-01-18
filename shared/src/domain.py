from pydantic import BaseModel
from typing import Dict, Any

class NewsItem(BaseModel):
    id: str
    title: str
    content: str
    summary: str
    source_url: str
    published_date: str
    metadata: Dict[str, Any]