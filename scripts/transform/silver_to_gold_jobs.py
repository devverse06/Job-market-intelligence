import json
from pathlib import Path
from datetime import datetime, timezone

from common.logger import get_logger
from common.contract_loader import load_contract

logger = get_logger("silver_to_gold")

SILVER_CANONICAL = Path("silver/jobs_canonical")
GOLD_DIR = Path("gold/jobs")
GOLD_DIR.mkdir(parents=True, exist_ok=True)

contract = load_contract("gold_job_contract.json")


def load_silver():
    records = []
    for f in SILVER_CANONICAL.glob("*.json"):
        records.extend(json.loads(f.read_text()))
    return records


def deduplicate(records):
    """
    Keep latest record per (job_id, source)
    """
    deduped = {}

    for r in records:
        key = (r["job_id"], r["source"])
        current = deduped.get(key)

        if not current or r["ingested_at"] > current["ingested_at"]:
            deduped[key] = r

    return list(deduped.values())


def validate_gold(job: dict) -> bool:
    for field in contract["required_fields"]:
        if field not in job or job[field] in (None, "", []):
            return False

    if len(job["description"]) < 100:
        return False

    return True


def run():
    silver_jobs = load_silver()
    logger.info(f"Loaded {len(silver_jobs)} Silver records")

    deduped = deduplicate(silver_jobs)
    logger.info(f"After deduplication: {len(deduped)}")

    gold_jobs = []

    for j in deduped:
        gold_job = j.copy()

        # Canonical rename
        gold_job["posted_date"] = gold_job.pop("posted_at", None)

        if validate_gold(gold_job):
            gold_jobs.append(gold_job)

    logger.info(f"Gold-valid records: {len(gold_jobs)}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out = GOLD_DIR / f"jobs_gold_{ts}.json"
    out.write_text(json.dumps(gold_jobs, indent=2))

    logger.info(f"Gold dataset written → {out}")


if __name__ == "__main__":
    run()