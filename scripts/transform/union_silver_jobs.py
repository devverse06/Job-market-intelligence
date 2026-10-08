import json
from pathlib import Path
from datetime import datetime, timezone

from common.logger import get_logger

logger = get_logger("union_silver_jobs")

SILVER_ADZUNA = Path("silver/adzuna/jobs")
SILVER_GREENHOUSE = Path("silver/greenhouse/jobs")
OUT_DIR = Path("silver/jobs_canonical")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_files(path: Path):
    records = []
    for f in path.glob("*.json"):
        records.extend(json.loads(f.read_text()))
    return records


def run():
    adzuna_jobs = load_files(SILVER_ADZUNA)
    greenhouse_jobs = load_files(SILVER_GREENHOUSE)

    all_jobs = adzuna_jobs + greenhouse_jobs

    # Hard safety check
    REQUIRED_KEYS = {
        "job_id",
        "source",
        "company",
        "title",
        "description",
        "location",
        "category",
        "ingested_at"
    }

    OPTIONAL_KEYS = {
        "posted_at",
        "posted_date",
        "salary_min",
        "salary_max",
        "apply_url",
        "latitude",
        "longitude"
    }

    def normalize(job: dict) -> dict:
        """
        Force canonical key names and fill missing optionals
        """
        return {
            "job_id": job["job_id"],
            "source": job["source"],
            "company": job["company"],
            "title": job["title"],
            "description": job["description"],
            "location": job["location"],
            "category": job["category"],
            "posted_date": job.get("posted_date") or job.get("posted_at"),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "apply_url": job.get("apply_url"),
            "latitude": job.get("latitude"),
            "longitude": job.get("longitude"),
            "ingested_at": job["ingested_at"]
        }

    canonical_jobs = []

    for j in all_jobs:
        if not REQUIRED_KEYS.issubset(j.keys()):
            raise ValueError(f"Missing required fields in job: {j.keys()}")

        canonical_jobs.append(normalize(j))

    out_file = OUT_DIR / f"jobs_canonical_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    out_file.write_text(json.dumps(all_jobs, indent=2))

    logger.info(f"Canonical Silver jobs written: {len(all_jobs)}")


if __name__ == "__main__":
    run()