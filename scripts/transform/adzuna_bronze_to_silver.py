import json
from pathlib import Path
from datetime import datetime, timezone

from common.logger import get_logger
from common.contract_loader import load_contract

logger = get_logger("adzuna_bronze_to_silver")

# Paths
RAW_DIR = Path("raw_data/adzuna")
SILVER_DIR = Path("silver/adzuna/jobs")
SILVER_DIR.mkdir(parents=True, exist_ok=True)

# Load Silver contract
contract = load_contract("adzuna_silver_contract.json")

def get_nested(obj: dict, path: str):
    """Safely extract nested fields like company.display_name"""
    value = obj
    for key in path.split("."):
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    return value

def normalize_job(job: dict) -> dict:
    return {
        "source": "adzuna",
        "job_id": job.get("id"),
        "title": (job.get("title") or "").strip(),
        "description": (job.get("description") or "").strip(),
        "company": get_nested(job, "company.display_name"),
        "location": get_nested(job, "location.display_name"),
        "category": get_nested(job, "category.label"),
        "posted_at": job.get("created"),
        "apply_url": job.get("redirect_url"),
        "salary_min": job.get("salary_min"),
        "salary_max": job.get("salary_max"),
        "latitude": job.get("latitude"),
        "longitude": job.get("longitude"),
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }

def validate_silver(job: dict) -> bool:
    for field in contract["required_fields"]:
        if field not in job or job[field] in (None, "", []):
            return False
    return True


def run():
    bronze_files = sorted(RAW_DIR.glob("adzuna_valid_*.json"))

    if not bronze_files:
        raise RuntimeError("No Bronze Adzuna files found")

    silver_records = []

    for file in bronze_files:
        logger.info(f"Processing {file.name}")
        data = json.loads(file.read_text())

        for raw_job in data:
            try:
                silver_job = normalize_job(raw_job)
                if validate_silver(silver_job):
                    silver_records.append(silver_job)
            except Exception as e:
                logger.warning(f"Skipped job due to error: {e}")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    output_file = SILVER_DIR / f"adzuna_jobs_silver_{timestamp}.json"

    output_file.write_text(json.dumps(silver_records, indent=2))
    logger.info(f"Silver jobs written: {len(silver_records)}")


if __name__ == "__main__":
    run()