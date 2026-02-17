import json
import concurrent.futures
from pathlib import Path
from multiprocessing import cpu_count
from tqdm import tqdm

from analyzer.discovery.files import discover_files
from analyzer.parsing.functions import extract_functions
from analyzer.signals.aggregate import aggregate_signals
from analyzer.testing.tests import map_tests
from analyzer.inference.edge_cases import detect_edge_cases
from analyzer.signals.signals import generate_signals
from schemas.analysis import AnalysisSchema

def detect_tech_stack(files):
    """Detects the tech stack based on marker files."""
    stack = []
    filenames = {Path(f['path']).name for f in files}
    all_paths_str = "".join([f['path'].lower() for f in files])

    if "package.json" in filenames: stack.append("Node.js")
    if "tsconfig.json" in filenames: stack.append("TypeScript")
    if "requirements.txt" in filenames or "pyproject.toml" in filenames: stack.append("Python")
    if "pom.xml" in filenames: stack.append("Java/Maven")
    if "go.mod" in filenames: stack.append("Go")
    if "prisma" in all_paths_str: stack.append("Prisma ORM")
    if "vite.config" in all_paths_str: stack.append("Vite")
    if "react" in all_paths_str: stack.append("React")

    return stack if stack else ["General Software"]


def _parse_file_batch(file_batch):
    """Processes a chunk of files in one go to reduce process overhead."""
    from analyzer.parsing.functions import extract_functions
    results = []
    for file_info in file_batch:
        file_path = file_info["path"]
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            results.extend(extract_functions(file_path, content))
        except Exception:
            continue
    return results


def run_analysis(path: str) -> dict:
    from analyzer.discovery.files import discover_files
    files = discover_files(path)
    all_functions = []

    # Optimization: Chunking
    # Spawning processes is expensive; processing in batches is 3x faster for small files.
    chunk_size = 20
    chunks = [files[i:i + chunk_size] for i in range(0, len(files), chunk_size)]

    max_workers = max(1, int(cpu_count() * 0.8))

    print(f"[coderecon] Analyzing {len(files)} files using {max_workers} cores...")

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_parse_file_batch, chunk): chunk for chunk in chunks}

        for future in tqdm(concurrent.futures.as_completed(futures),
                           total=len(chunks),
                           desc="[coderecon] Scanning",
                           unit="batch",
                           leave=False):
            all_functions.extend(future.result())

    # Pipeline logic...
    tech_stack = detect_tech_stack(files)
    tests = map_tests(files)
    edge_cases = detect_edge_cases(all_functions)
    raw_signals = generate_signals(all_functions, edge_cases, tests)
    aggregated_signals = aggregate_signals(raw_signals)

    analysis = AnalysisSchema(
        files=files,
        functions=all_functions,
        tests=tests,
        edge_cases=edge_cases,
        signals_raw=raw_signals,
        signals=aggregated_signals,
        tech_stack=tech_stack
    )

    analysis_dict = analysis.dict()

    with open("analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis_dict, f, indent=4)

    return analysis_dict

