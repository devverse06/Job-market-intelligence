import re


# -----------------------------------
# Seniority Classification
# -----------------------------------
def classify_seniority(title):
    title = title.lower()

    if "senior" in title:
        return "senior"
    elif "lead" in title:
        return "lead"
    elif "principal" in title:
        return "principal"
    elif "junior" in title:
        return "junior"
    else:
        return "mid"


# -----------------------------------
# Salary Band Classification
# -----------------------------------
def classify_salary_band(salary_min):
    if salary_min is None:
        return "unknown"

    if salary_min < 80000:
        return "low"
    elif salary_min < 130000:
        return "medium"
    elif salary_min < 180000:
        return "high"
    else:
        return "premium"

def classify_job_type(text):
    text = text.lower()

    if "remote" in text:
        return "remote"
    if "hybrid" in text:
        return "hybrid"
    return "onsite"


def run_enrichment(conn):

    # -----------------------------------
    # 1️⃣ Fetch all required data first
    # -----------------------------------
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                f.job_posting_key,
                f.salary_min,
                r.title,
                r.description
            FROM warehouse.fact_job_postings f
            JOIN raw.jobs_gold r
              ON f.job_id = r.job_id
             AND f.source = r.source
             AND f.ingested_at = r.ingested_at
        """)
        job_rows = cur.fetchall()

        cur.execute("""
            SELECT keyword, canonical_skill
            FROM warehouse.skill_dictionary
        """)
        skill_rows = cur.fetchall()

    # -----------------------------------
    # 2️⃣ Process enrichment
    # -----------------------------------
    with conn.cursor() as cur:

        for job_key, salary_min, title, description in job_rows:

            title = title or ""
            description = description or ""
            text_blob = f"{title} {description}".lower()
            job_type = classify_job_type(text_blob)

            # Seniority classification
            seniority = classify_seniority(title)
            salary_band = classify_salary_band(salary_min)

            cur.execute("""
                UPDATE warehouse.fact_job_postings
                SET seniority = %s,
                    salary_band = %s
                WHERE job_posting_key = %s
            """, (seniority, salary_band, job_key))

            # Get job_type_key
            cur.execute("""
                SELECT job_type_key
                FROM warehouse.dim_job_type
                WHERE job_type = %s
            """, (job_type,))
            result = cur.fetchone()

            if result:
                job_type_key = result[0]

                cur.execute("""
                    UPDATE warehouse.fact_job_postings
                    SET job_type_key = %s
                    WHERE job_posting_key = %s
                """, (job_type_key, job_key))

            # Skill extraction
            for keyword, canonical_skill in skill_rows:

                if keyword in text_blob:

                    # Insert into dim_skill
                    cur.execute("""
                        INSERT INTO warehouse.dim_skill (skill_name)
                        VALUES (%s)
                        ON CONFLICT (skill_name) DO NOTHING
                    """, (canonical_skill,))

                    # Fetch skill_key
                    cur.execute("""
                        SELECT skill_key
                        FROM warehouse.dim_skill
                        WHERE skill_name = %s
                    """, (canonical_skill,))
                    result = cur.fetchone()
                    if result:
                        skill_key = result[0]

                        # Insert bridge
                        cur.execute("""
                            INSERT INTO warehouse.bridge_job_skill
                            (job_posting_key, skill_key)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                        """, (job_key, skill_key))

    conn.commit()