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




def get_top_level_structure(path: str) -> str:
    """Generates a clean directory tree for the LLM to visualize the project layout."""
    try:
        root = Path(path)
        tree = []
        # Filter out heavy or irrelevant directories
        exclude = {".git", ".venv", "node_modules", "__pycache__", ".coderecon"}

        for item in sorted(root.iterdir()):
            if item.is_dir() and item.name not in exclude:
                tree.append(f"📁 {item.name}/")
                # Add a second level for clarity in large repos
                try:
                    for sub in sorted(item.iterdir()):
                        if sub.is_dir() and not sub.name.startswith("."):
                            tree.append(f"  └── 📁 {sub.name}/")
                        elif sub.is_file() and not sub.name.startswith("."):
                            tree.append(f"  └── 📄 {sub.name}")
                except PermissionError:
                    continue
            elif item.is_file() and not item.name.startswith("."):
                tree.append(f"📄 {item.name}")

        return "\n".join(tree[:40])  # Cap at 40 lines for context safety
    except Exception as e:
        return f"Structure discovery failed: {str(e)}"


def slice_for_explain_data(analysis_data, path):
    """
    High-density structural mapping.
    Prioritizes files with signals to focus LLM reasoning.
    """
    signals = analysis_data.get("signals", [])
    functions = analysis_data.get("functions", [])

    file_map = {}
    for f in functions:
        p = f['path'].replace(str(path), "").lstrip("\\/")
        if len(file_map) < 20:
            file_map.setdefault(p, []).append(f['name'])

    compact_logic = "\n".join([f"{k} => {', '.join(v)}" for k, v in file_map.items()])

    # If NO signals, do NOT return a 'CRITICAL SIGNALS' header.
    if not signals:
        return f"STRUCTURAL_MAP_ONLY:\n{compact_logic}"

    compact_signals = "\n".join([
        f"- [{s.get('rule_id', 'UNK')}] {s['type']} in {s.get('file', 'general')}: {s.get('message', '')}"
        for s in signals[:25]
    ])

    return f"STRUCTURAL MAP:\n{compact_logic}\n\nCRITICAL SIGNALS:\n{compact_signals}"