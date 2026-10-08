# Data Flow

## End-to-end flow
1. **Fetch**
   - Adzuna API → raw JSON files

2. **Normalize**
   - Raw → cleaned records (standard columns per source)

3. **Union**
   - Multi-source canonical dataset (schema aligned)

4. **Load warehouse**
   - Populate dimensions
   - Load fact table (incremental using ingestion watermark)

5. **Enrich**
   - Job type (remote/hybrid/onsite)
   - Seniority (jr/mid/senior)
   - Skills (bridge table)
   - Salary bands

6. **Metrics**
   - SQL views in `metrics` schema

7. **BI**
   - Power BI connects to `metrics.*` views

## Incremental logic
- The pipeline reads `warehouse.ingestion_state.last_success_ingested_at` per source.
- Only rows with `raw.jobs_gold.ingested_at > watermark` are loaded.
- On success, watermark advances to latest ingested timestamp.