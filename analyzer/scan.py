# analyzer/scan.py

from analyzer.discovery.files import discover_files
from analyzer.parsing.functions import extract_functions
from analyzer.signals.aggregate import aggregate_signals
from analyzer.testing.tests import map_tests
from analyzer.inference.edge_cases import detect_edge_cases
from analyzer.signals.signals import generate_signals
from schemas.analysis import AnalysisSchema


def run_analysis(path: str) -> dict:
    files = discover_files(path)
    functions = extract_functions(files)
    tests = map_tests(files)
    edge_cases = detect_edge_cases(functions)
    raw_signals = generate_signals(functions, edge_cases, tests)
    aggregated_signals = aggregate_signals(raw_signals)

    analysis = AnalysisSchema(
        files=files,
        functions=functions,
        tests=tests,
        edge_cases=edge_cases,
        signals_raw=raw_signals,
        signals = aggregated_signals
    )

    # IMPORTANT: return data, do not write files here
    return analysis.dict()
