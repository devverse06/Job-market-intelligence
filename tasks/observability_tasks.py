from datetime import date


def get_latest_ingested_at(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT MAX(ingested_at)
            FROM warehouse.fact_job_postings
        """)
        return cur.fetchone()[0]


def freshness_check(latest_posted_date, max_age_days=7):
    """
    Returns (freshness_ok, age_days)
    """
    if latest_posted_date is None:
        return False, None

    age_days = (date.today() - latest_posted_date).days
    return age_days <= max_age_days, age_days


def get_previous_success_counts(conn, current_run_id):
    """
    Returns (prev_raw_count, prev_fact_count) from the most recent SUCCESS run before current_run_id.
    """
    with conn.cursor() as cur:
        cur.execute("""
            SELECT raw_count, fact_count
            FROM warehouse.pipeline_runs
            WHERE status = 'success'
              AND run_id < %s
            ORDER BY run_id DESC
            LIMIT 1
        """, (current_run_id,))
        row = cur.fetchone()

    if not row:
        return None, None
    return row[0], row[1]


def volume_anomaly_check(curr_fact_count, prev_fact_count, drop_threshold=0.5, spike_threshold=2.0):
    """
    Returns (volume_ok, ratio)
    - Fails if curr is < (1-drop_threshold)*prev  OR  curr > spike_threshold*prev
    """
    if prev_fact_count is None or prev_fact_count == 0:
        return True, None  # no baseline yet

    ratio = curr_fact_count / prev_fact_count

    too_low = ratio < (1 - drop_threshold)      # e.g., drop_threshold=0.5 => ratio < 0.5 fails
    too_high = ratio > spike_threshold          # e.g., spike_threshold=2.0 => ratio > 2 fails

    return (not (too_low or too_high)), ratio