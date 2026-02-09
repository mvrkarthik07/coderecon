from collections import defaultdict


def aggregate_signals(signals):
    grouped = defaultdict(lambda: {
        "count": 0,
        "lines": set()
    })

    for sig in signals:
        key = (
            sig["type"],
            sig.get("path"),
            sig.get("function"),
            sig.get("case")
        )

        grouped[key]["count"] += 1

        if sig.get("line") is not None:
            grouped[key]["lines"].add(sig["line"])

    aggregated = []

    for (sig_type, path, function, case), data in grouped.items():
        aggregated.append({
            "type": sig_type,
            "path": path,
            "function": function,
            "case": case,
            "count": data["count"],
            "lines": sorted(data["lines"]),
        })

    return aggregated
