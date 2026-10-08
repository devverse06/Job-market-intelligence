import logging
from datetime import datetime
from pathlib import Path

from common.config import LOG_DIR

def get_logger(name: str):
    LOG_DIR.mkdir(exist_ok=True)

    log_file = LOG_DIR / f"{name}_{datetime.utcnow().date()}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger