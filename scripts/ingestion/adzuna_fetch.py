import requests
import json
from datetime import datetime
from pathlib import Path

from common.logger import get_logger
from common.contract_loader import load_contract
from common.config import RAW_DATA_DIR
from scripts.ingestion.config_adzuna import *

logger = get_logger("adzuna_ingest")
contract = load_contract("adzuna_job_contract.json")

RAW_DIR = Path("raw_data/adzuna")
RAW_DIR.mkdir(parents=True, exist_ok=True)

def fetch_page(page: int):
    url = f"{BASE_URL}/{COUNTRY}/search/{page}"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": "data engineer",
        "content-type": "application/json"
    }

    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()



def validate_schema(job: dict):
    # Required fields
    for field in contract["required_fields"]:
        if field not in job or job[field] in (None, "", []):
            return False

    # Description quality rule
    if len(job.get("description", "")) < 50:
        return False

    return True

def run():
    page = 1
    valid_jobs = []
    invalid_jobs = []

    while page <= 3:
        data = fetch_page(page)

        for job in data.get("results", []):
            if validate_schema(job):
                valid_jobs.append(job)
            else:
                invalid_jobs.append(job)

        page += 1

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    valid_file = RAW_DIR / f"adzuna_valid_{timestamp}.json"
    invalid_file = RAW_DIR / f"adzuna_invalid_{timestamp}.json"

    valid_file.write_text(json.dumps(valid_jobs, indent=2))
    invalid_file.write_text(json.dumps(invalid_jobs, indent=2))

    logger.info(f"Valid jobs written: {len(valid_jobs)}")
    logger.warning(f"Invalid jobs written: {len(invalid_jobs)}")

if __name__ == "__main__":
    run()