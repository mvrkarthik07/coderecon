# report/topology.py
from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path


# ---------------------------
# Helpers
# ---------------------------

def _top_module_name(mod: str | None) -> str | None:
    if not mod:
        return None
    return mod.split(".")[0]


def _collect_imports(py_file: str) -> set[str]:
    """
    Return set of top-level imported module names in a Python file.
    Best-effort; ignores parse failures.
    """
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
    """
    Mild heuristics: folder name cues.
    Returns: 'data', 'utils', 'llm', 'cli' or None
    """
    lp = p.replace("\\", "/").lower()
    parts = lp.split("/")
    if any(x in parts for x in ("schema", "schemas", "model", "models", "db", "database", "storage")):
        return "data"
    if any(x in parts for x in ("utils", "util", "helpers", "common", "report")):
        return "utils"
    if any(x in parts for x in ("llm", "mcp")):
        return "llm"
    if lp.endswith("cli.py") or lp.endswith("__main__.py"):
        return "cli"
    return None


def _risk_level(signal_count: int) -> str:
    if signal_count >= 8:
        return "High"
    if signal_count >= 3:
        return "Medium"
    return "Low"


def _risk_bar(count: int, max_count: int, width: int = 20) -> str:
    if max_count <= 0:
        return "█" * 1
    filled = max(1, int((count / max_count) * width))
    return "█" * filled


def _describe_file(path: str, fan_in: int, fan_out: int, signals: int, ext_imports: int) -> str:
    """
    Deterministic, short role-like description. No LLM.
    """
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
        # structural guess
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

    if extras:
        base += f" ({', '.join(extras)})"

    return base


# ---------------------------
# Core topology builder
# ---------------------------

def generate_topology(analysis: dict, repo_root: str | None = None, max_files_per_bucket: int = 9999) -> str:
    """
    Builds file-level topology from function call graph + signals, then returns a single text output.
    """
    functions = analysis.get("functions", [])
    signals = analysis.get("signals", [])
    files = analysis.get("files", [])

    # --- file list (paths) ---
    file_paths: list[str] = []
    for f in files:
        # your discover_files likely returns {"path": "..."}
        p = f.get("path") or f.get("file")
        if p:
            file_paths.append(str(p))

    # fallback: derive from functions
    if not file_paths:
        file_paths = sorted({fn.get("path") for fn in functions if fn.get("path")})

    # --- map function name -> defining file(s) ---
    fn_to_files: dict[str, set[str]] = defaultdict(set)
    for fn in functions:
        name = fn.get("name")
        p = fn.get("path") or fn.get("file")
        if name and p:
            fn_to_files[name].add(str(p))

    # --- build file-to-file dependency edges using internal function calls ---
    edges: set[tuple[str, str]] = set()
    ambiguous_calls = 0

    for fn in functions:
        src_file = fn.get("path") or fn.get("file")
        if not src_file:
            continue
        src_file = str(src_file)

        for called in fn.get("called_functions", []) or []:
            targets = fn_to_files.get(called, set())
            if not targets:
                continue

            # if multiple files define same function name, ambiguous; skip edge (safe)
            if len(targets) != 1:
                ambiguous_calls += 1
                continue

            dst_file = next(iter(targets))
            if dst_file != src_file:
                edges.add((src_file, dst_file))

    # --- fan-in / fan-out ---
    fan_out = defaultdict(int)
    fan_in = defaultdict(int)

    for a, b in edges:
        fan_out[a] += 1
        fan_in[b] += 1

    # ensure every file appears
    for p in file_paths:
        fan_out[p] += 0
        fan_in[p] += 0

    # --- signals per file ---
    file_signal_counts = defaultdict(int)
    for s in signals:
        p = s.get("path") or s.get("file")
        if p:
            file_signal_counts[str(p)] += 1

    # --- external integrations heuristic via imports ---
    # "external-heavy" doesn’t mean unsafe; it’s for bucketing.
    external_markers = {
        "requests", "httpx", "aiohttp", "boto3", "botocore", "subprocess",
        "selenium", "playwright", "openai", "anthropic", "google", "github",
        "git", "dotenv", "fastapi", "flask", "django"
    }

    file_imports = {}
    file_external_import_count = defaultdict(int)

    for p in file_paths:
        if not str(p).lower().endswith(".py"):
            continue
        imps = _collect_imports(p)
        file_imports[p] = imps
        file_external_import_count[p] = sum(1 for x in imps if x in external_markers)

    # --- bucket classification ---
    entry_points = []
    core = []
    data_layer = []
    utilities = []
    external_integrations = []
    others = []

    # thresholds scale with repo size (simple + robust)
    n_files = max(1, len(file_paths))
    core_in_th = 2 if n_files < 25 else 3
    core_out_th = 2 if n_files < 25 else 3

    for p in sorted(file_paths):
        si = file_signal_counts.get(p, 0)
        fi = fan_in.get(p, 0)
        fo = fan_out.get(p, 0)
        extc = file_external_import_count.get(p, 0)
        role_hint = _guess_role_from_path(p)

        if role_hint == "data":
            data_layer.append(p)
        elif extc >= 2 or role_hint == "llm":
            external_integrations.append(p)
        elif role_hint == "utils":
            utilities.append(p)
        elif fi == 0 and fo > 0:
            entry_points.append(p)
        elif fi >= core_in_th and fo >= core_out_th:
            core.append(p)
        else:
            others.append(p)

    # if core is empty, pick top central files by (fan_in+fan_out)
    if not core and file_paths:
        ranked = sorted(file_paths, key=lambda x: (fan_in[x] + fan_out[x], file_signal_counts[x]), reverse=True)
        core = ranked[: min(5, len(ranked))]

        # remove core from other buckets if it got included
        core_set = set(core)
        entry_points = [x for x in entry_points if x not in core_set]
        data_layer = [x for x in data_layer if x not in core_set]
        utilities = [x for x in utilities if x not in core_set]
        external_integrations = [x for x in external_integrations if x not in core_set]
        others = [x for x in others if x not in core_set]

    # --- pretty printing helpers ---
    def fmt_file(p: str) -> str:
        si = file_signal_counts.get(p, 0)
        fi = fan_in.get(p, 0)
        fo = fan_out.get(p, 0)
        extc = file_external_import_count.get(p, 0)
        risk = _risk_level(si)
        desc = _describe_file(p, fi, fo, si, extc)

        rel = p
        if repo_root:
            try:
                rel = str(Path(p).resolve().relative_to(Path(repo_root).resolve()))
            except Exception:
                rel = p

        return f"- {rel}\n    Role: {desc}\n    Risk: {risk} | Signals: {si} | Fan-in: {fi} | Fan-out: {fo}"

    def cap(lst: list[str]) -> list[str]:
        return lst[:max_files_per_bucket] if max_files_per_bucket > 0 else lst

    # --- build map + sections ---
    out_lines = []

    out_lines.append("ARCHITECTURAL TOPOLOGY MAP\n")
    out_lines.append("                [ Utilities ]")
    out_lines.append("                      ↑")
    out_lines.append("[ Entry Points ] → [ Core ] ← [ Data Layer ]")
    out_lines.append("                      ↓")
    out_lines.append("          [ External Integrations ]\n")

    # buckets
    def section(title: str, items: list[str]):
        out_lines.append(f"{title}")
        if not items:
            out_lines.append("  (none)\n")
            return
        for p in cap(items):
            out_lines.append("  " + fmt_file(p).replace("\n", "\n  "))
        if len(items) > len(cap(items)):
            out_lines.append(f"  ... ({len(items) - len(cap(items))} more)\n")
        else:
            out_lines.append("")

    section("ENTRY POINTS", entry_points)
    section("CORE", core)
    section("DATA LAYER", data_layer)
    section("UTILITIES", utilities)
    section("EXTERNAL INTEGRATIONS", external_integrations)

    # everything else (still included)
    section("OTHER FILES", others)

    # risk heatmap
    out_lines.append("\nRISK HEATMAP (by signal count)\n")

    all_counts = [(p, file_signal_counts.get(p, 0)) for p in file_paths]
    all_counts.sort(key=lambda x: x[1], reverse=True)

    max_count = all_counts[0][1] if all_counts else 0

    # show all files in heatmap (your request), but still readable
    for p, c in all_counts:
        risk = _risk_level(c)
        bar = _risk_bar(c, max_count, width=20)
        rel = p
        if repo_root:
            try:
                rel = str(Path(p).resolve().relative_to(Path(repo_root).resolve()))
            except Exception:
                rel = p
        out_lines.append(f"{risk:<6} {bar:<20} {c:>3}  {rel}")

    if ambiguous_calls:
        out_lines.append(f"\nNOTE: {ambiguous_calls} ambiguous function-name calls were skipped (same function name defined in multiple files).")

    return "\n".join(out_lines)
