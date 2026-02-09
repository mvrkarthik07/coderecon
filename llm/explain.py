from pathlib import Path
import json


def slice_by_file(analysis_path: str, target_path: str) -> dict:
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    signals = [
        s for s in analysis["signals"]
        if s.get("path") == target_path
    ]

    return {
        "path": target_path,
        "signal_count": len(signals),
        "signals": signals,
    }
