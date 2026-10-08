import psycopg2

def populate_dim_company(conn):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO warehouse.dim_company (company_name, source)
            SELECT DISTINCT company_name, source
            FROM raw.jobs_gold
            WHERE company_name IS NOT NULL
            ON CONFLICT (company_name, source) DO NOTHING;
        """)
    conn.commit()


def populate_dim_location(conn):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO warehouse.dim_location (city, county, is_remote)
            SELECT DISTINCT city, county, is_remote
            FROM raw.jobs_gold
            ON CONFLICT (city, county, is_remote) DO NOTHING;
        """)
    conn.commit()


def populate_dim_time(conn):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO warehouse.dim_time (date_key, date, year, month, week)
            SELECT DISTINCT
                TO_CHAR(posted_date, 'YYYYMMDD')::INT AS date_key,
                posted_date,
                EXTRACT(YEAR FROM posted_date),
                EXTRACT(MONTH FROM posted_date),
                EXTRACT(WEEK FROM posted_date)
            FROM raw.jobs_gold
            WHERE posted_date IS NOT NULL
            ON CONFLICT (date_key) DO NOTHING;
        """)
    conn.commit()


def populate_fact(conn, source, last_ts):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO warehouse.fact_job_postings (
                job_id,
                source,
                company_key,
                location_key,
                posted_date_key,
                salary_min,
                salary_max,
                ingested_at,
                title_key
            )
            SELECT
                g.job_id,
                g.source,
                c.company_key,
                l.location_key,
                d.date_key,
                g.salary_min,
                g.salary_max,
                g.ingested_at,
                t.title_key
            FROM raw.jobs_gold g
            JOIN warehouse.dim_company c
                ON g.company_name = c.company_name
            JOIN warehouse.dim_location l
                ON g.city = l.city
            JOIN warehouse.dim_date d
                ON d.full_date = g.posted_date::date
            JOIN warehouse.dim_title t
                ON LOWER(g.title) = LOWER(t.title)
            WHERE g.source = %s
              AND (%s IS NULL OR g.ingested_at > %s)
            ON CONFLICT (job_id, source, ingested_at) DO NOTHING;
        """, (source, last_ts, last_ts))
    conn.commit()