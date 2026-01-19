import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOG_DIR = Path("logs")
LOG_FILE_PATH = LOG_DIR / "app.log"
FILE_LOG_FORMAT = "%(filename)s:%(lineno)d - %(asctime)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
CONSOLE_LOG_FORMAT = "%(message)s"

def setup_logging():
    """
    This function runs at app startup (main.py).
    Task: Create folders and clean up old logs as required.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    return True

def get_logger(module_name: str) -> logging.Logger:
    """
    Creates a logger for each module
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG) 
    logger.propagate = False

    if logger.handlers:
        return logger

    file_handler = RotatingFileHandler(
        LOG_DIR / "app.log", 
        maxBytes=5_000_000,
        backupCount=3, 
        encoding="utf-8"
    )
    file_formatter = logging.Formatter("%(filename)s:%(lineno)d - %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.INFO)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter("%(levelname)s: [%(name)s] %(message)s")
    stream_handler.setFormatter(stream_formatter)
    stream_handler.setLevel(logging.DEBUG)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger