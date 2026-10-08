# Warehouse Schema (Star Schema)

## Fact table
### warehouse.fact_job_postings
**Grain:** 1 job posting per source per ingestion timestamp  
**Keys:** (job_id, source, ingested_at) unique

Contains:
- company_key
- location_key
- posted_date_key
- title_key
- salary_min, salary_max
- enrichment fields: job_type_key, salary_band_key, seniority
- ingested_at

## Dimensions
- warehouse.dim_company(company_key, company_name, source)
- warehouse.dim_location(location_key, city, county, is_remote)
- warehouse.dim_date(date_key, full_date, year, month, day)
- warehouse.dim_title(title_key, title)
- warehouse.dim_job_type(job_type_key, job_type)
- warehouse.dim_salary_band(salary_band_key, salary_band)
- warehouse.dim_skill(skill_key, skill_name)

## Bridge
- warehouse.bridge_job_skill(job_posting_key, skill_key)
  - many-to-many: one job can contain multiple skills