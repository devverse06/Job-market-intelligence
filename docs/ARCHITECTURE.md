# Job Market Intelligence Platform — Architecture

## Goal
Provide an automated, analytics-ready job market dataset (jobs, salary, skills, seniority, job type) and expose executive metrics to Power BI.

## High-level components
1. **Sources**
   - Adzuna API (jobs search)
   - Greenhouse (optional/expandable)

2. **Ingestion + Storage (Raw / Bronze)**
   - Python ingestion scripts pull API payloads
   - Raw JSON stored for replay/debugging

3. **Normalization (Silver)**
   - Source-specific cleanup + schema enforcement
   - Canonical union across sources (schema drift protection)

4. **Warehouse (PostgreSQL)**
   - Star schema:
     - `warehouse.fact_job_postings`
     - dimensions: company, location, date, title, job_type, salary_band, skill
     - bridge: job_posting ↔ skill

5. **Enrichment**
   - Seniority classification
   - Job type classification (remote/hybrid/onsite)
   - Skill extraction (keyword table-driven)
   - Salary band mapping

6. **Metrics layer**
   - `metrics.*` SQL views: trends, top companies/locations, skill growth, salary intelligence

7. **Consumption**
   - Power BI connects to Postgres views (`metrics.*`)
   - Executive dashboard pages: Overview / Salary / Skills / Company

8. **Automation + Observability**
   - Daily cron schedule
   - `warehouse.pipeline_runs` stores run metadata and quality checks
   - `warehouse.ingestion_state` stores incremental watermark (per source)
   - Logs written to `logs/pipeline.log` and `logs/cron.log`

## Non-goals (current version)
- Cloud deployment (Phase 8)
- Airflow/Prefect orchestration (future enhancement)
- Great Expectations suite (future enhancement)