import json
from common.config import CONTRACT_DIR

def load_contract(contract_name: str) -> dict:
    path = CONTRACT_DIR / contract_name
    if not path.exists():
        raise FileNotFoundError(f"Contract not found: {path}")

    with open(path, "r") as f:
        return json.load(f)