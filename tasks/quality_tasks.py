def validate_row_counts(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                (SELECT COUNT(*) FROM raw.jobs_gold),
                (SELECT COUNT(*) FROM warehouse.fact_job_postings);
        """)
        raw_count, fact_count = cur.fetchone()

    if fact_count > raw_count:
        raise Exception("Fact count exceeds raw count!")

    return raw_count, fact_count


def validate_no_orphans(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*)
            FROM warehouse.fact_job_postings f
            LEFT JOIN warehouse.dim_company c
            ON f.company_key = c.company_key
            WHERE c.company_key IS NULL;
        """)
        orphans = cur.fetchone()[0]

    if orphans > 0:
        raise Exception("Orphan company keys found!")

    return orphans