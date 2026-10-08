import os

BASE_URL = "https://api.adzuna.com/v1/api/jobs"
COUNTRY = "us"
RESULTS_PER_PAGE = 50

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")

if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
    raise RuntimeError("ADZUNA_APP_ID or ADZUNA_APP_KEY not set in environment")