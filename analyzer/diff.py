import json
from pathlib import Path


def run_diff_logic():
    # Use the same root where analysis.json lives
    current_path = Path("analysis.json")
    previous_path = Path("analysis_previous.json")

    if not previous_path.exists():
        return "[coderecon] Diff Refused: No previous analysis found. Run 'scan' twice to compare changes."

    with open(current_path, "r", encoding="utf-8") as f:
        curr = json.load(f)
    with open(previous_path, "r", encoding="utf-8") as f:
        prev = json.load(f)

    # Use Path + Type + Message as the unique signature for a signal
    def get_sig(s):
        return (s.get("path") or s.get("file"), s.get("type"), s.get("message"))

    curr_set = {get_sig(s) for s in curr.get("signals", [])}
    prev_set = {get_sig(s) for s in prev.get("signals", [])}

    added = curr_set - prev_set
    removed = prev_set - curr_set

    # Formatting Output
    out = ["# 🔄 RECON DELTA REPORT\n"]

    if added:
        out.append(f"## 🛑 New Hazards Detected (+{len(added)})")
        for path, stype, msg in added:
            out.append(f"- [{stype.upper()}] in {path}: {msg}")

    if removed:
        out.append(f"\n## ✅ Risks Resolved (-{len(removed)})")
        for path, stype, msg in removed:
            out.append(f"- Resolved: {stype} in {path}")

    if not added and not removed:
        out.append("No changes in signal density detected.")

    return "\n".join(out)