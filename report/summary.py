from collections import Counter

def run_summary(analysis: dict):
    files = analysis.get("files", [])
    functions = analysis.get("functions", [])
    tests = analysis.get("tests", [])
    signals = analysis.get("signals", [])

    severity_counts = Counter(
        s.get("severity", "Low") for s in signals
    )

    signal_types = Counter(
        s.get("type") for s in signals
    )

    test_ratio = len(tests) / len(functions) if functions else 0

    print("\n=== Coderecon Summary ===")
    print(f"Files: {len(files)}")
    print(f"Functions: {len(functions)}")
    print(f"Tests: {len(tests)}")
    print(f"Test Ratio: {round(test_ratio, 3)}")
    print("\nSignal Distribution:")
    for k, v in signal_types.items():
        print(f"  {k}: {v}")
    print("\nSeverity Distribution:")
    for k, v in severity_counts.items():
        print(f"  {k}: {v}")
