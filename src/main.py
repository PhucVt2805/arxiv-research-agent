from src.utils.log_config import setup_logging, get_logger
from src.crawler.scraper import ArxivScraper

setup_logging()

logger = get_logger("System")

logger.info("Server đang khởi động...")

scraper = ArxivScraper()
papers = scraper.get_paper(topics=["AI"], days_back=2)
for p in papers[:3]:
    logger.info(f'Paper ID: {p.id}, Title: {p.title}, Updated: {p.updated_date}')