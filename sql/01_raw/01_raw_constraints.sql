-- RAW constraints: prevent duplicates at source level
ALTER TABLE raw.jobs_gold
ADD CONSTRAINT IF NOT EXISTS unique_raw_job
UNIQUE (job_id, source, ingested_at);

-- Optional: raw columns you added during project
ALTER TABLE raw.jobs_gold
ADD COLUMN IF NOT EXISTS title TEXT;

ALTER TABLE raw.jobs_gold
ADD COLUMN IF NOT EXISTS description TEXT;