import json
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict

from common.logger import get_logger

logger = get_logger("gold_to_analytics")

GOLD_DIR = Path("gold/jobs")
OUT_DIR = Path("gold/analytics")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def load_gold():
    records = []
    for f in GOLD_DIR.glob("jobs_gold_*.json"):
        records.extend(json.loads(f.read_text()))
    return records


def run():
    jobs = load_gold()
    logger.info(f"Loaded {len(jobs)} Gold jobs")

    # -------- Feature 1: Jobs by Location --------
    jobs_by_location = Counter(j["location"] for j in jobs)

    # -------- Feature 2: Jobs by Company --------
    jobs_by_company = Counter(j["company"] for j in jobs)

    # -------- Feature 3: Salary Stats --------
    salaries = [
        (j.get("salary_min"), j.get("salary_max"))
        for j in jobs
        if j.get("salary_min") and j.get("salary_max")
    ]

    salary_stats = {
        "count": len(salaries),
        "avg_min_salary": round(sum(s[0] for s in salaries) / len(salaries), 2) if salaries else None,
        "avg_max_salary": round(sum(s[1] for s in salaries) / len(salaries), 2) if salaries else None,
    }

    analytics = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_jobs": len(jobs),
        "jobs_by_location": jobs_by_location.most_common(20),
        "jobs_by_company": jobs_by_company.most_common(20),
        "salary_stats": salary_stats,
    }

    out_file = OUT_DIR / f"job_market_analytics_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    out_file.write_text(json.dumps(analytics, indent=2))

    logger.info(f"Analytics dataset written → {out_file}")


if __name__ == "__main__":
    run()