from fastmcp import FastMCP
from analyzer.scan import run_analysis
from analyzer.inference.edge_cases import detect_edge_cases
import json
import os

mcp = FastMCP("Coderecon")


@mcp.tool()
def get_codebase_signals(path: str):
    """Returns deterministic risk signals (nesting, complexity, hazards) for a path."""
    # We run the actual analyzer logic here
    analysis = run_analysis(path)
    return json.dumps(analysis.get("signals", []), indent=2)


@mcp.tool()
def get_hotspots(path: str):
    """Returns the top 3 most complex/risky files based on signal density."""
    analysis = run_analysis(path)
    # Logic to count signals per file
    files = analysis.get("files", [])
    signals = analysis.get("signals", [])

    stats = {}
    for s in signals:
        file = s.get("file")
        stats[file] = stats.get(file, 0) + 1

    sorted_hotspots = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:3]
    return f"Top Hotspots: {sorted_hotspots}"


if __name__ == "__main__":
    mcp.run()