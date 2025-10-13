import json
from pathlib import Path
from dataclasses import asdict, is_dataclass
from enum import Enum
from datetime import datetime
from core.constants import DATA_DIR, FILE_MAP, COUNTER_FILE

class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, datetime):
            return o.isoformat()
        if is_dataclass(o):
            return asdict(o) # type: ignore[arg-type]
        return super().default(o)
    
def initialize_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    for data_type in FILE_MAP:
        if not FILE_MAP[data_type].exists():
            save_json(FILE_MAP[data_type], [])
    if not COUNTER_FILE.exists():
        with COUNTER_FILE.open("w", encoding="utf-8") as f:
            f.write("0")

def load_json(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: Path, data: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, cls=EnhancedJSONEncoder)

def load_data(data_type: str) -> list[dict]:
    return load_json(FILE_MAP[data_type])

def save_data(data_type: str, data: list[dict]) -> None:
    save_json(FILE_MAP[data_type], data)

