import json
from pathlib import Path
from datetime import datetime
import psycopg2
# ----------------------------
# 1. Database connection
# ----------------------------
conn = psycopg2.connect(
    dbname="job_market_dw",
    user="postgres",        # <-- change this
    password="Vinoth@1997",# <-- change this
    host="localhost",
    port=5432
)
cur = conn.cursor()
# ----------------------------
# 2. Locate Gold files safely
# ----------------------------
BASE_DIR = Path(__file__).resolve().parents[2]
gold_dir = BASE_DIR / "gold" / "jobs"
gold_files = list(gold_dir.glob("jobs_gold_*.json"))
print(f"Found {len(gold_files)} gold files")


total_rows_inserted = 0


# ----------------------------
# 3. Process each file
# ----------------------------
for file in gold_files:
    with open(file) as f:
        jobs = json.load(f)

    file_row_count = 0

    for job in jobs:

        # ----------------------------
        # Field Mapping
        # ----------------------------
        job_id = job.get("job_id")
        source = job.get("source")
        company_name = job.get("company")

        # Parse location safely
        location_raw = job.get("location")
        city = None
        county = None

        if location_raw:
            parts = [p.strip() for p in location_raw.split(",")]
            if len(parts) >= 1:
                city = parts[0]
            if len(parts) >= 2:
                county = parts[1]

        # Convert posted_date to DATE
        posted_date = None
        if job.get("posted_date"):
            try:
                posted_date = datetime.fromisoformat(
                    job["posted_date"].replace("Z", "+00:00")
                ).date()
            except Exception:
                posted_date = None

        # Convert ingested_at to TIMESTAMP
        ingested_at = None
        if job.get("ingested_at"):
            try:
                ingested_at = datetime.fromisoformat(job["ingested_at"])
            except Exception:
                ingested_at = None

        salary_min = job.get("salary_min")
        salary_max = job.get("salary_max")

        # ----------------------------
        # Insert into raw.jobs_gold
        # ----------------------------
        cur.execute(
            """
            INSERT INTO raw.jobs_gold (
                job_id,
                source,
                company_name,
                city,
                county,
                is_remote,
                posted_date,
                salary_min,
                salary_max,
                ingested_at,
                title,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id, source, ingested_at) DO NOTHING
            """,
            (
                job_id,
                source,
                company_name,
                city,
                county,
                False,
                posted_date,
                salary_min,
                salary_max,
                ingested_at,
                job.get("title"),
                job.get("description")
            )
        )

        file_row_count += 1
        total_rows_inserted += 1

    print(f"Inserted {file_row_count} rows from {file.name}")


# ----------------------------
# 4. Commit & Close
# ----------------------------
conn.commit()
cur.close()
conn.close()

print(f"Total rows inserted: {total_rows_inserted}")