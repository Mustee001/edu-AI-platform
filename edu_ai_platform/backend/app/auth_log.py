from datetime import datetime
from pathlib import Path
import json
from typing import List, Dict, Any

LOG_DIR = Path(__file__).resolve().parents[1] / "logs"
LOG_FILE = LOG_DIR / "auth_events.jsonl"


def _ensure_log_dir():
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def record_event(event_data: Dict[str, Any]) -> None:
    _ensure_log_dir()
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        **event_data
    }
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")
    except Exception:
        pass


def recent_events(limit: int = 100) -> List[Dict[str, Any]]:
    _ensure_log_dir()
    if not LOG_FILE.exists():
        return []

    events = []
    try:
        with LOG_FILE.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                try:
                    event = json.loads(line.strip())
                    events.append(event)
                except Exception:
                    continue
    except Exception:
        pass

    return events
