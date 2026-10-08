from datetime import datetime


def get_last_success_ingested_at(conn, source):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT last_success_ingested_at
            FROM warehouse.ingestion_state
            WHERE source = %s
        """, (source,))
        row = cur.fetchone()
        return row[0] if row else None


def update_last_success_ingested_at(conn, source, timestamp, run_id):
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE warehouse.ingestion_state
            SET last_success_ingested_at = %s,
                last_success_run_id = %s,
                updated_at = NOW()
            WHERE source = %s
        """, (timestamp, run_id, source))
    conn.commit()