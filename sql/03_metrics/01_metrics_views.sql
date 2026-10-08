-- Executive overview
CREATE OR REPLACE VIEW metrics.total_job_postings AS
SELECT COUNT(*) AS total_jobs
FROM warehouse.fact_job_postings;

CREATE OR REPLACE VIEW metrics.jobs_by_day AS
SELECT
    t.date,
    COUNT(f.job_posting_key) AS job_count
FROM warehouse.fact_job_postings f
JOIN warehouse.dim_time t
    ON f.posted_date_key = t.date_key
GROUP BY t.date
ORDER BY t.date;

CREATE OR REPLACE VIEW metrics.monthly_job_postings AS
SELECT
    t.year,
    t.month,
    COUNT(*) AS job_count
FROM warehouse.fact_job_postings f
JOIN warehouse.dim_time t
    ON f.posted_date_key = t.date_key
GROUP BY t.year, t.month
ORDER BY t.year, t.month;

-- Companies / locations
CREATE OR REPLACE VIEW metrics.top_hiring_companies AS
SELECT
    c.company_name,
    COUNT(*) AS job_count
FROM warehouse.fact_job_postings f
JOIN warehouse.dim_company c
    ON f.company_key = c.company_key
GROUP BY c.company_name
ORDER BY job_count DESC;

CREATE OR REPLACE VIEW metrics.demand_by_location AS
SELECT
    l.city,
    l.county,
    COUNT(*) AS job_count
FROM warehouse.fact_job_postings f
JOIN warehouse.dim_location l
    ON f.location_key = l.location_key
GROUP BY l.city, l.county
ORDER BY job_count DESC;

-- Job type
CREATE OR REPLACE VIEW metrics.job_type_distribution AS
SELECT
    jt.job_type,
    COUNT(*) AS job_count,
    ROUND(
        COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (),
        2
    ) AS percentage
FROM warehouse.fact_job_postings f
JOIN warehouse.dim_job_type jt
    ON f.job_type_key = jt.job_type_key
GROUP BY jt.job_type
ORDER BY job_count DESC;

-- Salary intelligence
CREATE OR REPLACE VIEW metrics.avg_salary_by_seniority AS
SELECT
    seniority,
    ROUND(AVG(salary_min), 2) AS avg_salary
FROM warehouse.fact_job_postings
WHERE salary_min IS NOT NULL
GROUP BY seniority
ORDER BY avg_salary DESC;

-- If you later add dim_title + title_key mapping, upgrade this view to GROUP BY title.
-- For now, keep a safe global avg salary view:
CREATE OR REPLACE VIEW metrics.avg_salary_overall AS
SELECT
    ROUND(AVG(salary_min), 2) AS avg_salary_min,
    ROUND(AVG(salary_max), 2) AS avg_salary_max
FROM warehouse.fact_job_postings
WHERE salary_min IS NOT NULL;

-- Skills
CREATE OR REPLACE VIEW metrics.skill_demand AS
SELECT
    s.skill_name,
    COUNT(*) AS job_count
FROM warehouse.bridge_job_skill b
JOIN warehouse.dim_skill s
ON b.skill_key = s.skill_key
GROUP BY s.skill_name
ORDER BY job_count DESC;

CREATE OR REPLACE VIEW metrics.seniority_distribution AS
SELECT
    seniority,
    COUNT(*) AS job_count
FROM warehouse.fact_job_postings
GROUP BY seniority
ORDER BY job_count DESC;

CREATE OR REPLACE VIEW metrics.skill_demand_by_seniority AS
SELECT
  s.skill_name,
  f.seniority,
  COUNT(*) AS job_count
FROM warehouse.bridge_job_skill b
JOIN warehouse.fact_job_postings f ON b.job_posting_key = f.job_posting_key
JOIN warehouse.dim_skill s ON b.skill_key = s.skill_key
GROUP BY s.skill_name, f.seniority
ORDER BY s.skill_name;

-- Monthly skill trend
CREATE OR REPLACE VIEW metrics.skill_monthly_trend AS
SELECT
  t.year,
  t.month,
  s.skill_name,
  COUNT(*) AS job_count
FROM warehouse.bridge_job_skill b
JOIN warehouse.dim_skill s ON b.skill_key = s.skill_key
JOIN warehouse.fact_job_postings f ON b.job_posting_key = f.job_posting_key
JOIN warehouse.dim_time t ON f.posted_date_key = t.date_key
GROUP BY t.year, t.month, s.skill_name
ORDER BY t.year, t.month, job_count DESC;

-- Skill growth
CREATE OR REPLACE VIEW metrics.skill_growth AS
WITH monthly AS (
    SELECT
      t.year,
      t.month,
      s.skill_name,
      COUNT(*) AS job_count
    FROM warehouse.bridge_job_skill b
    JOIN warehouse.dim_skill s ON b.skill_key = s.skill_key
    JOIN warehouse.fact_job_postings f ON b.job_posting_key = f.job_posting_key
    JOIN warehouse.dim_time t ON f.posted_date_key = t.date_key
    GROUP BY t.year, t.month, s.skill_name
)
SELECT
  year,
  month,
  skill_name,
  job_count,
  job_count - LAG(job_count) OVER (PARTITION BY skill_name ORDER BY year, month) AS month_over_month_change
FROM monthly
ORDER BY skill_name, year, month;

CREATE OR REPLACE VIEW metrics.top_growing_skills AS
SELECT *
FROM (
    SELECT
      skill_name,
      SUM(month_over_month_change) AS total_growth
    FROM metrics.skill_growth
    WHERE month_over_month_change IS NOT NULL
    GROUP BY skill_name
) growth
ORDER BY total_growth DESC;

CREATE OR REPLACE VIEW metrics.skill_rolling_3m AS
WITH monthly AS (
    SELECT
      t.year,
      t.month,
      s.skill_name,
      COUNT(*) AS job_count
    FROM warehouse.bridge_job_skill b
    JOIN warehouse.dim_skill s ON b.skill_key = s.skill_key
    JOIN warehouse.fact_job_postings f ON b.job_posting_key = f.job_posting_key
    JOIN warehouse.dim_time t ON f.posted_date_key = t.date_key
    GROUP BY t.year, t.month, s.skill_name
)
SELECT
  year,
  month,
  skill_name,
  job_count,
  AVG(job_count) OVER (
    PARTITION BY skill_name
    ORDER BY year, month
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  ) AS rolling_3m_avg
FROM monthly
ORDER BY skill_name, year, month;