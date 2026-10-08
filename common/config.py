from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = BASE_DIR / "raw_data"
LOG_DIR = BASE_DIR / "logs"
CONTRACT_DIR = BASE_DIR / "contracts"

RAW_DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)