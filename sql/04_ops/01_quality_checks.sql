-- Row counts: raw vs fact
SELECT
  (SELECT COUNT(*) FROM raw.jobs_gold) AS raw_count,
  (SELECT COUNT(*) FROM warehouse.fact_job_postings) AS fact_count;

-- Orphans checks
SELECT COUNT(*)
FROM warehouse.fact_job_postings f
LEFT JOIN warehouse.dim_company c ON f.company_key = c.company_key
WHERE c.company_key IS NULL;

SELECT COUNT(*)
FROM warehouse.fact_job_postings f
LEFT JOIN warehouse.dim_location l ON f.location_key = l.location_key
WHERE l.location_key IS NULL;

SELECT COUNT(*)
FROM warehouse.fact_job_postings f
LEFT JOIN warehouse.dim_time t ON f.posted_date_key = t.date_key
WHERE t.date_key IS NULL;

-- Null critical keys
SELECT COUNT(*)
FROM warehouse.fact_job_postings
WHERE job_id IS NULL
   OR source IS NULL
   OR company_key IS NULL
   OR location_key IS NULL
   OR posted_date_key IS NULL;

-- Latest ingestion timestamp (freshness)
SELECT MAX(ingested_at) AS latest_ingested_at
FROM warehouse.fact_job_postings;