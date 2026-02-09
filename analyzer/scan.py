# analyzer/scan.py
import json
from pathlib import Path

from analyzer.discovery.files import discover_files
from analyzer.parsing.functions import extract_functions
from analyzer.testing.tests import map_tests
from analyzer.inference.edge_cases import detect_edge_cases
from analyzer.signals.signals import generate_signals
from schemas.analysis import AnalysisSchema

def run_analysis(path: str):
    files = discover_files(path)
    functions = extract_functions(files)
    tests = map_tests(files)
    edge_cases = detect_edge_cases(functions)
    signals = generate_signals(functions, edge_cases, tests)

    analysis = AnalysisSchema(
        files=files,
        functions=functions,
        tests=tests,
        edge_cases=edge_cases,
        signals=signals
    )

    out = Path(".coderecon")
    out.mkdir(exist_ok=True)

    with open(out / "analysis.json", "w") as f:
        json.dump(analysis.dict(), f, indent=2)

    print("✔ Scan complete")
    print(f"✔ Files scanned: {len(files)}")
    print(f"✔ Functions detected: {len(functions)}")
    print(f"✔ Tests detected: {len(tests)}")
    print(f"✔ Edge cases inferred: {len(edge_cases)}")
    print(f"✔ Signals generated: {len(signals)}")
    print("Analysis saved to .coderecon/analysis.json")
