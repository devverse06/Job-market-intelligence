-- Insert into fact from raw (idempotent)
INSERT INTO warehouse.fact_job_postings (
    job_id,
    source,
    company_key,
    location_key,
    posted_date_key,
    salary_min,
    salary_max,
    ingested_at
)
SELECT
    r.job_id,
    r.source,
    c.company_key,
    l.location_key,
    t.date_key,
    r.salary_min,
    r.salary_max,
    r.ingested_at
FROM raw.jobs_gold r
JOIN warehouse.dim_company c
    ON r.company_name = c.company_name
   AND r.source = c.source
JOIN warehouse.dim_location l
    ON r.city IS NOT DISTINCT FROM l.city
   AND r.county IS NOT DISTINCT FROM l.county
   AND r.is_remote IS NOT DISTINCT FROM l.is_remote
JOIN warehouse.dim_time t
    ON r.posted_date = t.date
ON CONFLICT (job_id, source, ingested_at) DO NOTHING;

-- Salary band key mapping
UPDATE warehouse.fact_job_postings f
SET salary_band_key = d.salary_band_key
FROM warehouse.dim_salary_band d
WHERE COALESCE(f.salary_band, 'unknown') = d.salary_band;

-- Job type mapping (remote vs onsite based on raw.is_remote)
UPDATE warehouse.fact_job_postings f
SET job_type_key = jt.job_type_key
FROM warehouse.dim_job_type jt
WHERE jt.job_type =
  CASE WHEN EXISTS (
        SELECT 1
        FROM raw.jobs_gold r
        WHERE r.job_id = f.job_id
          AND r.source = f.source
          AND r.ingested_at = f.ingested_at
          AND r.is_remote = true
  )
  THEN 'remote'
  ELSE 'onsite'
  END;