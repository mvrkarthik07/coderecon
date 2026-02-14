def assign_severity(signal_type: str) -> str:
    mapping = {
        "untested_function": "Medium",
        "potential_edge_case": "Low",
        "exception_path": "High",
        "division_operation": "High",
        "while_loop": "Medium",
        "conditional_branch": "Low"
    }

    return mapping.get(signal_type, "Low")

def generate_signals(functions, edge_cases, tests):
    """Convert raw findings into structured signals."""

    signals = []

    tested_functions = set()
    for test in tests:
        tested_functions.update(test["references"])

    # Untested functions
    for fn in functions:
        if fn["length"] > 100:
            signals.append({
                "type": "large_function",
                "function": fn["name"],
                "path": fn["path"],
                "line": fn["line_start"],
                "length": fn["length"],
                "severity": "High"
            })
        elif fn["length"] > 60:
            signals.append({
                "type": "large_function",
                "function": fn["name"],
                "path": fn["path"],
                "line": fn["line_start"],
                "length": fn["length"],
                "severity": "Medium"
            })
        if fn["name"] not in tested_functions:
            signal_type = "untested_function"
            signals.append({
                "type": "untested_function",
                "function": fn["name"],
                "path": fn["path"],
                "line": fn["line_start"],
                "severity": assign_severity(signal_type),
            })

    # Potential edge cases
    for ec in edge_cases:
        signal_type = "potential_edge_case"
        signals.append({
            "type": "potential_edge_case",
            "function": ec["function"],
            "path": ec["file"],
            "line": ec.get("line"),
            "case": ec["case"],
            "rule_id": ec.get("rule_id"),
            "node_type": ec.get("node_type"),
            "severity": assign_severity(signal_type),
        })

    return signals
