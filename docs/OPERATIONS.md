# Operations (Automation + Monitoring)

## How pipeline runs
- Scheduled via cron daily at 7:00 AM:
  - Runs: `python -m pipelines.job_market_pipeline`
  - Output appended to: `logs/cron.log`
  - Structured logs written to: `logs/pipeline.log`

## Observability tables
### warehouse.pipeline_runs
Tracks:
- start_time / end_time
- status (running/success/failed)
- raw_count / fact_count
- duration_seconds
- freshness_ok / volume_ok
- error_message

### warehouse.ingestion_state
Tracks incremental watermarks:
- source
- last_success_ingested_at
- last_success_run_id

## Quality checks
- Row count sanity check (raw vs fact)
- Orphan checks for foreign keys
- Freshness check (latest ingested date threshold)
- Volume anomaly check (spike/drop vs last successful run)