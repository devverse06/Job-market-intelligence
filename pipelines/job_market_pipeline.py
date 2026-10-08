import logging
import os

LOG_DIR = os.path.join(os.getcwd(), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

import psycopg2
from tasks.enrichment_tasks import run_enrichment
from datetime import datetime
import time




from tasks.warehouse_tasks import (
    populate_dim_company,
    populate_dim_location,
    populate_dim_time,
    populate_fact
)

from tasks.quality_tasks import (
    validate_row_counts,
    validate_no_orphans
)

from tasks.observability_tasks import (
    get_latest_ingested_at,
    freshness_check,
    get_previous_success_counts,
    volume_anomaly_check
)

from tasks.incremental_state import (
    get_last_success_ingested_at,
    update_last_success_ingested_at
)

def run_pipeline():
    print("Pipeline started")
    conn = psycopg2.connect(
        dbname="job_market_dw",
        user="postgres",
        password="Vinoth1997",
        host="job-market-dw.cva688coogtz.us-east-2.rds.amazonaws.com",
        port=5432,
        sslmode="require"
    )
    print("Connected to DB successfully")
    run_id = None
    start_ts = time.time()

    try:
        with conn.cursor() as cur:
            # Insert pipeline run start record
            cur.execute("""
                INSERT INTO warehouse.pipeline_runs (start_time, status)
                VALUES (NOW(), 'running')
                RETURNING run_id;
            """)
            run_id = cur.fetchone()[0]
        conn.commit()

        logger.info(f"Pipeline run_id={run_id} started.")
        print(f"Pipeline run_id={run_id} started.")

        # ----------------------------
        # Incremental cutoff timestamp
        # ----------------------------
        source = "adzuna"  # for now we do one source. later we expand to both.
        last_ts = get_last_success_ingested_at(conn, source)

        print(f"[INCREMENTAL] last_success_ingested_at for {source} = {last_ts}")

        # ----------------------------
        # Execute Tasks
        # ----------------------------
        logger.info("Populating fact table...")
        print("Populating fact table...")
        populate_fact(conn, source, last_ts)

        logger.info("Running enrichment...")
        print("Running enrichment...")
        run_enrichment(conn)

        print("Running quality checks...")
        raw_count, fact_count = validate_row_counts(conn)
        validate_no_orphans(conn)

        latest_ingested = get_latest_ingested_at(conn)
        fresh_ok, age_days = freshness_check(latest_ingested.date(), max_age_days=30)

        prev_raw, prev_fact = get_previous_success_counts(conn, run_id)
        vol_ok, ratio = volume_anomaly_check(fact_count, prev_fact, drop_threshold=0.5, spike_threshold=2.0)

        duration_seconds = int(time.time() - start_ts)

        if not fresh_ok:
            raise Exception(f"Freshness check failed: latest_posted_date={latest_ingested} age_days={age_days}")

        if not vol_ok:
            raise Exception(f"Volume anomaly failed: prev_fact={prev_fact} curr_fact={fact_count} ratio={ratio}")

        # ----------------------------
        # Mark Success
        # ----------------------------
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE warehouse.pipeline_runs
                SET
                    end_time = NOW(),
                    status = 'success',
                    raw_count = %s,
                    fact_count = %s,
                    duration_seconds = %s,
                    latest_posted_date = %s,
                    freshness_ok = %s,
                    volume_ok = %s
                WHERE run_id = %s;
            """, (
                raw_count,
                fact_count,
                duration_seconds,
                latest_ingested,
                fresh_ok,
                vol_ok,
                run_id
            ))
        conn.commit()

        update_last_success_ingested_at(conn, source, latest_ingested, run_id)

        logger.info(f"Pipeline successful. Raw: {raw_count}, Fact: {fact_count}")
        print(f"Pipeline successful. Raw: {raw_count}, Fact: {fact_count}")

    except Exception as e:

        error_message = str(e)

        if run_id is not None:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE warehouse.pipeline_runs
                    SET
                        end_time = NOW(),
                        status = 'failed',
                        error_message = %s
                    WHERE run_id = %s;
                """, (error_message, run_id))
            conn.commit()

        logger.error(error_message)
        print("Pipeline failed:", error_message)
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    run_pipeline()