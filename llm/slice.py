from pathlib import Path
import json


def slice_by_directory(analysis_path: str, target_dir: str) -> dict:
    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    base = Path(target_dir).resolve()

    signals = []
    files = set()

    for s in analysis["signals"]:
        path = s.get("path")

        if not path:
            continue  # skip malformed signals safely

        p = Path(path).resolve()

        if base in p.parents:
            signals.append(s)
            files.add(path)

    return {
        "directory": str(base),
        "file_count": len(files),
        "signal_count": len(signals),
        "signals": signals,
    }
