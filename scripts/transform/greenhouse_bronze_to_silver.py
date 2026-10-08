import json
from datetime import datetime, timezone
from pathlib import Path

from common.logger import get_logger

logger = get_logger("greenhouse_to_silver")

RAW_DIR = Path("raw_data/greenhouse")
SILVER_DIR = Path("silver/greenhouse/jobs")
SILVER_DIR.mkdir(parents=True, exist_ok=True)


def normalize(job: dict) -> dict:
    return {
        "job_id": job.get("id"),
        "source": "greenhouse",
        "company": job.get("source_company"),
        "title": job.get("title"),
        "description": job.get("content"),
        "location": job.get("location", {}).get("name"),
        "category": job.get("departments", [{}])[0].get("name"),
        "posted_date": job.get("updated_at"),
        "salary_min": None,
        "salary_max": None,
        "ingested_at": datetime.now(timezone.utc).isoformat()
    }


def run():
    files = list(RAW_DIR.glob("greenhouse_raw_*.json"))
    if not files:
        raise RuntimeError("No Greenhouse raw files found")

    all_silver = []

    for file in files:
        data = json.loads(file.read_text())
        for job in data:
            all_silver.append(normalize(job))

    out_file = SILVER_DIR / f"greenhouse_silver_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    out_file.write_text(json.dumps(all_silver, indent=2))

    logger.info(f"Silver Greenhouse records written: {len(all_silver)}")


if __name__ == "__main__":
    run()