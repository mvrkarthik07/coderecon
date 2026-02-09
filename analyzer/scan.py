# analyzer/scan.py

from analyzer.discovery.files import discover_files
from analyzer.parsing.functions import extract_functions
from analyzer.testing.tests import map_tests
from analyzer.inference.edge_cases import detect_edge_cases
from analyzer.signals.signals import generate_signals
from schemas.analysis import AnalysisSchema


def run_analysis(path: str) -> dict:
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

    # IMPORTANT: return data, do not write files here
    return analysis.dict()
