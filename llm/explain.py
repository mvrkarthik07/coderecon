from pathlib import Path
import json
from collections import Counter

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
from pathlib import Path
import json


def slice_for_explain(analysis_path: str, target: str) -> dict:
    """
    Slice analysis.json for:
    - single file
    - directory
    - entire project (.)
    """

    with open(analysis_path, "r", encoding="utf-8") as f:
        analysis = json.load(f)

    signals = analysis.get("signals", [])

    target_path = Path(target).resolve()

    # If target is ".", treat as full codebase
    if target == ".":
        valid_signals = [
            s for s in signals
            if s.get("path") is not None
        ]

        severity_counts = Counter(s.get("severity", "unknown") for s in valid_signals)
        return {
            "mode": "directory",
            "directory": str(target_path),
            "file_count": len(set(s["path"] for s in valid_signals)),
            "signal_count": len(valid_signals),
            "signals": valid_signals,
            "severity_counts": dict(severity_counts),
        }

    # If directory
    if target_path.is_dir():
        selected = []
        files = set()

        for s in signals:
            path = s.get("path")
            if not path:
                continue

            p = Path(path).resolve()

            if target_path in p.parents:
                selected.append(s)
                files.add(path)
        severity_counts = Counter(s.get("severity", "unknown") for s in selected)
        return {
            "mode": "directory",
            "directory": str(target_path),
            "file_count": len(files),
            "signal_count": len(selected),
            "signals": selected,
            "severity_counts": dict(severity_counts),
        }

    # Otherwise treat as file
    selected = [
        s for s in signals
        if s.get("path") and Path(s["path"]).resolve() == target_path
    ]
    severity_counts = Counter(s.get("severity", "unknown") for s in selected)

    return {
        "mode": "file",
        "path": str(target_path),
        "signal_count": len(selected),
        "signals": selected,
        "severity_counts":dict(severity_counts),
    }



def slice_for_explain_data(analysis: dict, target: str) -> dict:
    signals = analysis.get("signals", [])
    target_path = Path(target).resolve()

    # System mode
    if target == ".":
        valid = [s for s in signals if s.get("path")]

        severity_counts = Counter(
            s.get("severity", "Low") for s in valid
        )

        return {
            "mode": "system",
            "directory": str(target_path),
            "file_count": len(set(s["path"] for s in valid)),
            "signal_count": len(valid),
            "severity_counts": dict(severity_counts),
            "signals": valid,
        }

    # Directory mode
    if target_path.is_dir():
        selected = []
        files = set()

        for s in signals:
            path = s.get("path")
            if not path:
                continue

            p = Path(path).resolve()

            if target_path in p.parents:
                selected.append(s)
                files.add(path)

        severity_counts = Counter(
            s.get("severity", "Low") for s in selected
        )

        return {
            "mode": "directory",
            "directory": str(target_path),
            "file_count": len(files),
            "signal_count": len(selected),
            "severity_counts": dict(severity_counts),
            "signals": selected,
        }

    # File mode
    selected = [
        s for s in signals
        if s.get("path") and Path(s["path"]).resolve() == target_path
    ]

    return {
        "mode": "file",
        "path": str(target_path),
        "signal_count": len(selected),
        "signals": selected,
    }
