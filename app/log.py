import json
import time
from pathlib import Path

LOG = Path(__file__).parent.parent / "logs" / "turns.jsonl"


def log_turn(**fields):
    LOG.parent.mkdir(exist_ok=True)
    fields["ts"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with LOG.open("a") as f:
        f.write(json.dumps(fields) + "\n")
