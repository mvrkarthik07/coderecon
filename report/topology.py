from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path
import os


# ---------------------------
# Helpers
# ---------------------------

def _norm(p: str) -> str:
    """Standardize path strings for reliable dictionary lookups."""
    if not p:
        return ""
    # Normalize slashes, remove redundant dots, and lowercase for Windows case-insensitivity
    return os.path.normpath(p).lower()


def _top_module_name(mod: str | None) -> str | None:
    if not mod:
        return None
    return mod.split(".")[0]


def _collect_imports(py_file: str) -> set[str]:
    """Return set of top-level imported module names in a Python file."""
    imports: set[str] = set()
    try:
        src = Path(py_file).read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except Exception:
        return imports

    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                top = _top_module_name(a.name)
                if top:
                    imports.add(top)
        elif isinstance(n, ast.ImportFrom):
            top = _top_module_name(n.module)
            if top:
                imports.add(top)
    return imports


def _guess_role_from_path(p: str) -> str | None:
    lp = p.replace("\\", "/").lower()
    parts = lp.split("/")
    if any(x in parts for x in ("schema", "schemas", "model", "models", "db", "database", "storage")):
        return "data"
    if any(x in parts for x in ("utils", "util", "helpers", "common", "report", "reporting")):
        return "utils"
    if any(x in parts for x in ("llm", "mcp", "ai", "inference")):
        return "llm"
    if lp.endswith("cli.py") or lp.endswith("__main__.py") or lp.endswith("main.py"):
        return "cli"
    return None


def _risk_level(signal_count: int) -> str:
    if signal_count >= 15:
        return "High"
    if signal_count >= 5:
        return "Medium"
    return "Low"


def _risk_bar(count: int, max_count: int, width: int = 20) -> str:
    if max_count <= 0:
        return "█"
    filled = max(1, int((count / max_count) * width))
    return "█" * filled


def _describe_file(path: str, fan_in: int, fan_out: int, signals: int, ext_imports: int) -> str:
    role_hint = _guess_role_from_path(path)
    if role_hint == "cli":
        base = "Command/entry dispatcher"
    elif role_hint == "llm":
        base = "LLM/MCP integration layer"
    elif role_hint == "data":
        base = "Data/schema layer"
    elif role_hint == "utils":
        base = "Utility/reporting layer"
    else:
        if fan_in == 0 and fan_out > 0:
            base = "Entry-style coordinator"
        elif fan_in > 0 and fan_out > 0:
            base = "Core processing module"
        elif fan_out == 0 and fan_in > 0:
            base = "Leaf/helper module"
        else:
            base = "Support module"

    extras = []
    if ext_imports >= 3:
        extras.append("external-heavy")
    if fan_out >= 8:
        extras.append("wide-orchestrator")
    if fan_in >= 8:
        extras.append("central-dependency")
    return f"{base} ({', '.join(extras)})" if extras else base


# ---------------------------
# Core topology builder
# ---------------------------

def generate_topology(analysis: dict, repo_root: str | None = None, max_files_per_bucket: int = 9999) -> str:
    functions = analysis.get("functions", [])
    signals = analysis.get("signals", [])
    files = analysis.get("files", [])

    # 1. Collect and Normalize File Paths
    normalized_paths: list[str] = []
    norm_to_orig: dict[str, str] = {} # Map normalized path back to original for display

    for f in files:
        p = f.get("path") or f.get("file")
        if p:
            n = _norm(str(p))
            normalized_paths.append(n)
            norm_to_orig[n] = str(p)

    # 2. Map signals using normalized keys
    file_signal_counts = defaultdict(int)
    for s in signals:
        p = s.get("path") or s.get("file")
        if p:
            file_signal_counts[_norm(str(p))] += 1

    # 3. Build Dependency Map
    fn_to_files: dict[str, set[str]] = defaultdict(set)
    for fn in functions:
        name, p = fn.get("name"), fn.get("path") or fn.get("file")
        if name and p:
            fn_to_files[name].add(_norm(str(p)))

    edges: set[tuple[str, str]] = set()
    for fn in functions:
        src_file = _norm(str(fn.get("path") or fn.get("file") or ""))
        if not src_file: continue
        for called in fn.get("called_functions", []) or []:
            targets = fn_to_files.get(called, set())
            if len(targets) == 1:
                dst_file = next(iter(targets))
                if dst_file != src_file:
                    edges.add((src_file, dst_file))

    fan_out, fan_in = defaultdict(int), defaultdict(int)
    for a, b in edges:
        fan_out[a] += 1
        fan_in[b] += 1

    # 4. External Heuristics
    external_markers = {"requests", "httpx", "aiohttp", "boto3", "subprocess", "openai", "os", "sys"}
    file_ext_count = defaultdict(int)
    for n_p in normalized_paths:
        orig_p = norm_to_orig[n_p]
        if orig_p.endswith(".py"):
            imps = _collect_imports(orig_p)
            file_ext_count[n_p] = sum(1 for x in imps if x in external_markers)

    # 5. Bucketing logic
    buckets = {k: [] for k in ["ENTRY POINTS", "CORE", "DATA LAYER", "UTILITIES", "EXTERNAL INTEGRATIONS", "OTHERS"]}
    n_files = max(1, len(normalized_paths))
    core_th = 2 if n_files < 25 else 3

    for n_p in sorted(normalized_paths):
        orig_p = norm_to_orig[n_p]
        role = _guess_role_from_path(orig_p)
        fi, fo = fan_in[n_p], fan_out[n_p]
        extc = file_ext_count[n_p]

        if role == "cli" or (fi == 0 and fo > 0):
            buckets["ENTRY POINTS"].append(n_p)
        elif role == "data":
            buckets["DATA LAYER"].append(n_p)
        elif role == "llm" or extc >= 2:
            buckets["EXTERNAL INTEGRATIONS"].append(n_p)
        elif role == "utils":
            buckets["UTILITIES"].append(n_p)
        elif fi >= core_th and fo >= core_th:
            buckets["CORE"].append(n_p)
        else:
            buckets["OTHERS"].append(n_p)

    # Output Construction
    out = ["ARCHITECTURAL TOPOLOGY MAP\n",
           "                [ Utilities ]",
           "                      ↑",
           "[ Entry Points ] → [ Core ] ← [ Data Layer ]",
           "                      ↓",
           "          [ External Integrations ]\n"]

    def fmt_file(n_p: str) -> str:
        orig_p = norm_to_orig[n_p]
        si, fi, fo = file_signal_counts[n_p], fan_in[n_p], fan_out[n_p]
        extc = file_ext_count[n_p]
        rel = orig_p.replace(str(repo_root or ""), "").lstrip("\\/")
        return f"- {rel}\n    Role: {_describe_file(orig_p, fi, fo, si, extc)}\n    Risk: {_risk_level(si)} | Signals: {si} | Fan-in: {fi} | Fan-out: {fo}"

    for title, items in buckets.items():
        out.append(title)
        if not items:
            out.append("  (none)\n")
        else:
            for n_p in items[:max_files_per_bucket]:
                out.append("  " + fmt_file(n_p).replace("\n", "\n  "))
            out.append("")

    out.append("\nRISK HEATMAP (by signal count)\n")
    all_counts = sorted([(n_p, file_signal_counts[n_p]) for n_p in normalized_paths], key=lambda x: x[1], reverse=True)
    max_count = all_counts[0][1] if all_counts else 0

    for n_p, c in all_counts:
        risk = _risk_level(c)
        bar = _risk_bar(c, max_count)
        rel = norm_to_orig[n_p].replace(str(repo_root or ""), "").lstrip("\\/")
        out.append(f"{risk:<7} {bar:<20} {c:>3}  {rel}")

    return "\n".join(out)