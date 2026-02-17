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
    """Convert raw findings into structured signals with safety fallbacks."""

    signals = []

    tested_functions = set()
    for test in tests:
        # Safely handle potential missing references key
        tested_functions.update(test.get("references", []))

    # Untested functions
    for fn in functions:
        # Use .get() to prevent KeyError if 'length' or 'line_start' is missing
        length = fn.get("length", 0)
        line_start = fn.get("line_start", fn.get("line", 0)) # Fallback to 'line' for regex matches
        fn_name = fn.get("name", "unknown")
        fn_path = fn.get("path", "unknown")

        # Threshold checks with safe length
        if length > 100:
            signals.append({
                "type": "large_function",
                "function": fn_name,
                "path": fn_path,
                "line": line_start,
                "length": length,
                "severity": "High"
            })
        elif length > 60:
            signals.append({
                "type": "large_function",
                "function": fn_name,
                "path": fn_path,
                "line": line_start,
                "length": length,
                "severity": "Medium"
            })

        if fn_name not in tested_functions:
            signal_type = "untested_function"
            signals.append({
                "type": "untested_function",
                "function": fn_name,
                "path": fn_path,
                "line": line_start,
                "severity": assign_severity(signal_type),
            })

    # Potential edge cases
    for ec in edge_cases:
        signal_type = "potential_edge_case"
        signals.append({
            "type": "potential_edge_case",
            "function": ec.get("function"),
            "path": ec.get("file"),
            "line": ec.get("line"),
            "case": ec.get("case"),
            "rule_id": ec.get("rule_id"),
            "node_type": ec.get("node_type"),
            "severity": assign_severity(signal_type),
        })

    return signals