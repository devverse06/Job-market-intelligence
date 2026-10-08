import requests
import json
from datetime import datetime, timezone
from pathlib import Path

from common.logger import get_logger

logger = get_logger("greenhouse_ingest")

RAW_DIR = Path("raw_data/greenhouse")
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Example companies using Greenhouse
COMPANY_BOARDS = {
    "stripe": "stripe",
    "airbnb": "airbnb",
    "databricks": "databricks"
}

BASE_URL = "https://boards-api.greenhouse.io/v1/boards"


def fetch_company_jobs(company: str):
    url = f"{BASE_URL}/{company}/jobs"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()["jobs"]


def run():
    all_jobs = []

    for company, board in COMPANY_BOARDS.items():
        logger.info(f"Fetching jobs for {company}")
        jobs = fetch_company_jobs(board)
        for job in jobs:
            job["source_company"] = company
            all_jobs.append(job)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output_file = RAW_DIR / f"greenhouse_raw_{timestamp}.json"

    output_file.write_text(json.dumps(all_jobs, indent=2))
    logger.info(f"Greenhouse jobs written: {len(all_jobs)}")


if __name__ == "__main__":
    run()