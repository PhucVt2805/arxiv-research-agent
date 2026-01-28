import arxiv
from ast import List
from src.model import ArxivPaper
from typing import Literal, List, Optional
from src.utils.log_config import get_logger
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone, timedelta

logger = get_logger("Crawler") 

class ArxivScraper:
    def __init__(self):
        self.client = arxiv.Client(
                page_size = 100,
                delay_seconds = 3,
                num_retries = 3
            )

    def get_paper(
            self,
            topics: List[Literal["AI", "AR", "CC", "CE", "CL", "CR", "CV", "CY", "DB", "DC", "DL", "DM", "DS", "ET", "GR", "GT", "HC", "IR", "IT", "LO", "LG", "MA", "MM", "MS", "NA", "NE", "NI", "OS", "PF", "PL", "RO", "SC", "SD", "SE", "SI", "SY"]] = "AI",
            keyword: str = '',
            days_back: Optional[int] = 3,
            start_date: Optional[str] = None
        ) -> list[ArxivPaper]:
        """Get recent papers from arXiv based on topic, keyword and date.
        
        Args:
            topic (Literal): The research area to filter papers. Defaults to "AI".
                includes:
                    AI: Artificial Intelligence
                    AR: Hardware Architecture
                    CC: Computational Complexity
                    CE: Computational Engineering, Finance, and Science
                    CL: Computation and Language
                    CR: Cryptography and Security
                    CV: Computer Vision and Pattern Recognition
                    CY: Computers and Society
                    DB: Databases
                    DC: Distributed, Parallel, and Cluster Computing
                    DL: Digital Libraries
                    DM: Discrete Mathematics
                    DS: Data Structures and Algorithms
                    ET: Emerging Technologies
                    GR: Graphics
                    GT: Computer Science and Game Theory
                    HC: Human-Computer Interaction
                    IR: Information Retrieval
                    IT: Information Theory
                    LO: Logic in Computer Science
                    LG: Machine Learning
                    MA: Multiagent Systems
                    MM: Multimedia
                    MS: Mathematical Software
                    NA: Numerical Analysis
                    NE: Neural and Evolutionary Computing
                    NI: Networking and Internet Architecture
                    OS: Operating Systems
                    PF: Performance
                    PL: Programming Languages
                    RO: Robotics
                    SC: Symbolic Computation
                    SD: Sound
                    SE: Software Engineering
                    SI: Social and Information Networks
                    SY: Systems and Control

            keyword: Keywords used to search for content users are interested in.
            days_back: Number of days to start searching for content. Calculated as: today's date - days_back

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing paper details.
        """
        
        logger.info(f"🔍 Crawling Keyword: '{keyword}' | Topics: {topics}")
        if start_date:
            try:
                dt = datetime.strptime(start_date, "%Y-%m-%d")
                cutoff_date = dt.replace(tzinfo=timezone.utc)
                logger.info(f"🔍 Research Mode: Lấy bài từ ngày {cutoff_date}")
            except ValueError:
                logger.error("Format ngày sai, fallback về days_back")
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        elif days_back:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max(days_back, 1))
        else:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        today = datetime.now(timezone.utc).date()

        if not topics:
            cat_part = 'cat:cs.*'
        else:
            cat_part = "(" + " OR ".join([f"cat:cs.{t}" for t in topics]) + ")"

        if keyword.strip():
            x = keyword.strip().replace('"', '')
            key_part = f'all:"{x}"'

            query = f'{key_part} AND {cat_part}'
        else:
            query = cat_part

        logger.info(f'📡 Arxiv Query: {query}')

        search = arxiv.Search(
            query = query,
            max_results = 300 if keyword else 100,
            sort_by = arxiv.SortCriterion.LastUpdatedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        results_list = []
        seen_ids = set()

        try:
            for result in self.client.results(search):
                if result.updated.date() > today - cutoff_date: continue
                short_id = result.entry_id.split('/')[-1]

                if short_id in seen_ids: continue
                seen_ids.add(short_id)

                paper = ArxivPaper(
                    _id = result.entry_id.split('/')[-1],
                    title = result.title.replace('\n', ' '),
                    author = [str(a) for a in result.authors],
                    arxiv_url = result.entry_id,
                    pdf_url=result.pdf_url,
                    published_date=result.published,
                    updated_date=result.updated,
                    summary = result.summary.replace('\n', ' '),
                    prime_category = result.primary_category,
                    categories = result.categories
                )
                results_list.append(paper)
                
        except Exception as e:
            logger.error(f'Error fetching papers: {e}')
        
        logger.info(f'Found {len(results_list)} papers updated in the last {days_back} days in topics: {topics}')

        return results_list
    
    async def save_to_db(self, papers: List[ArxivPaper]) -> List[ArxivPaper]:
        """An asynchronous function to save to MongoDB via Beanie.
        Returns the number of new posts added."""
        if not papers:
            logger.info("No new papers to save.")
            return []
        
        new_papers = []
        logger.info('Start saving to the database...')

        for paper in papers:
            try:
                await paper.insert()
                new_papers.append(paper)
                logger.debug(f'Add {paper.id} to the database')
            except DuplicateKeyError:
                pass
            except Exception as e:
                logger.error(f'Error saving paper ID {paper.id}: {e}')

        logger.info(f'✅ Saved {len(new_papers)} new papers to the Mongodb.')
        return new_papers