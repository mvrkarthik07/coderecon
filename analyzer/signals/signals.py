def generate_signals(functions, edge_cases, tests):
    """Convert raw findings into structured signals."""

    signals = []

    tested_functions = set()
    for test in tests:
        tested_functions.update(test["references"])

    # Untested functions
    for fn in functions:
        if fn["name"] not in tested_functions:
            signals.append({
                "type": "untested_function",
                "function": fn["name"],
                "file": fn["file"],
                "line": fn["line_start"]
            })

    # Potential edge cases
    for ec in edge_cases:
        signals.append({
            "type": "potential_edge_case",
            "function": ec["function"],
            "file": ec["file"],
            "line": ec.get("line"),
            "case": ec["case"],
            "rule_id": ec.get("rule_id"),
            "node_type": ec.get("node_type")
        })

    return signals
