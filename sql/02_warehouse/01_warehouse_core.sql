-- FACT constraints: prevent duplicates at warehouse level
ALTER TABLE warehouse.fact_job_postings
ADD CONSTRAINT IF NOT EXISTS unique_fact_job
UNIQUE (job_id, source, ingested_at);

-- Pipeline run logging table
CREATE TABLE IF NOT EXISTS warehouse.pipeline_runs (
    run_id SERIAL PRIMARY KEY,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status TEXT NOT NULL,
    raw_count INT,
    fact_count INT,
    error_message TEXT,
    duration_seconds INT,
    latest_posted_date DATE,
    freshness_ok BOOLEAN,
    volume_ok BOOLEAN
);

-- Incremental ingestion state table
CREATE TABLE IF NOT EXISTS warehouse.ingestion_state (
    source TEXT PRIMARY KEY,
    last_success_ingested_at TIMESTAMP NULL,
    last_success_run_id BIGINT NULL,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

INSERT INTO warehouse.ingestion_state (source)
VALUES ('adzuna'), ('greenhouse')
ON CONFLICT (source) DO NOTHING;

-- Skill dimension + bridge
CREATE TABLE IF NOT EXISTS warehouse.dim_skill (
    skill_key SERIAL PRIMARY KEY,
    skill_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS warehouse.bridge_job_skill (
    job_posting_key INT,
    skill_key INT,
    PRIMARY KEY (job_posting_key, skill_key),
    FOREIGN KEY (job_posting_key) REFERENCES warehouse.fact_job_postings(job_posting_key),
    FOREIGN KEY (skill_key) REFERENCES warehouse.dim_skill(skill_key)
);

-- Enrichment columns in fact
ALTER TABLE warehouse.fact_job_postings
ADD COLUMN IF NOT EXISTS seniority TEXT;

ALTER TABLE warehouse.fact_job_postings
ADD COLUMN IF NOT EXISTS salary_band TEXT;

-- Salary band + job type dimensions
CREATE TABLE IF NOT EXISTS warehouse.dim_salary_band (
    salary_band_key SERIAL PRIMARY KEY,
    salary_band TEXT UNIQUE NOT NULL
);

INSERT INTO warehouse.dim_salary_band (salary_band)
VALUES ('low'), ('medium'), ('high'), ('premium'), ('unknown')
ON CONFLICT (salary_band) DO NOTHING;

CREATE TABLE IF NOT EXISTS warehouse.dim_job_type (
    job_type_key SERIAL PRIMARY KEY,
    job_type TEXT UNIQUE NOT NULL
);

INSERT INTO warehouse.dim_job_type (job_type)
VALUES ('remote'), ('onsite'), ('hybrid'), ('unknown')
ON CONFLICT (job_type) DO NOTHING;

-- Add keys to fact
ALTER TABLE warehouse.fact_job_postings
ADD COLUMN IF NOT EXISTS salary_band_key INT,
ADD COLUMN IF NOT EXISTS job_type_key INT;

-- FK constraints
ALTER TABLE warehouse.fact_job_postings
ADD CONSTRAINT IF NOT EXISTS fk_fact_salary_band
FOREIGN KEY (salary_band_key) REFERENCES warehouse.dim_salary_band(salary_band_key);

ALTER TABLE warehouse.fact_job_postings
ADD CONSTRAINT IF NOT EXISTS fk_fact_job_type
FOREIGN KEY (job_type_key) REFERENCES warehouse.dim_job_type(job_type_key);

-- Dictionary for skill extraction
CREATE TABLE IF NOT EXISTS warehouse.skill_dictionary (
    keyword TEXT PRIMARY KEY,
    canonical_skill TEXT NOT NULL
);

INSERT INTO warehouse.skill_dictionary (keyword, canonical_skill)
VALUES
('python', 'Python'),
('sql', 'SQL'),
('spark', 'Spark'),
('azure', 'Azure'),
('aws', 'AWS'),
('airflow', 'Airflow'),
('snowflake', 'Snowflake'),
('databricks', 'Databricks'),
('pandas', 'Pandas')
ON CONFLICT (keyword) DO NOTHING;