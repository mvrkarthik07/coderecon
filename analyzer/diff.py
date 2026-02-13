import json
from pathlib import Path


def compute_diff():
    base = Path(".coderecon")
    current = base / "analysis.json"
    previous = base / "analysis_previous.json"

    if not previous.exists():
        return {"error": "No previous analysis found."}

    with open(current, "r", encoding="utf-8") as f:
        curr = json.load(f)

    with open(previous, "r", encoding="utf-8") as f:
        prev = json.load(f)

    curr_set = {
        (s.get("path"), s.get("type"), s.get("function"))
        for s in curr["signals"]
    }

    prev_set = {
        (s.get("path"), s.get("type"), s.get("function"))
        for s in prev["signals"]
    }

    added = curr_set - prev_set
    removed = prev_set - curr_set

    return {
        "added": list(added),
        "removed": list(removed),
        "added_count": len(added),
        "removed_count": len(removed),
    }
