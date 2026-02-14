from graphviz import Digraph
from collections import defaultdict


def generate_graph(analysis: dict):
    functions = analysis.get("functions", [])
    signals = analysis.get("signals", [])

    dot = Digraph(comment="CodeRecon Architecture")
    dot.attr(rankdir="LR", bgcolor="#111111")
    dot.attr("node", style="filled", fontcolor="white")

    defined_functions = {fn["name"] for fn in functions}

    # Risk map
    risk_map = defaultdict(int)
    for s in signals:
        fn = s.get("function")
        if fn:
            risk_map[fn] += 1

    fan_out = defaultdict(int)
    fan_in = defaultdict(int)

    for fn in functions:
        for called in fn.get("called_functions", []):
            if called in defined_functions:
                fan_out[fn["name"]] += 1
                fan_in[called] += 1

    # Group by file
    file_groups = defaultdict(list)
    for fn in functions:
        file_groups[fn["path"]].append(fn)

    # Create clusters per file
    for file_name, fns in file_groups.items():
        with dot.subgraph(name=f"cluster_{file_name}") as c:
            c.attr(label=file_name, color="gray")

            for fn in fns:
                name = fn["name"]
                risk = risk_map.get(name, 0)
                out_degree = fan_out.get(name, 0)

                # Color logic
                if out_degree >= 5:
                    color = "purple"
                elif risk >= 5:
                    color = "red"
                elif risk >= 2:
                    color = "orange"
                else:
                    color = "#4da6ff"

                c.node(name, fillcolor=color)

    # Edges
    for fn in functions:
        for called in fn.get("called_functions", []):
            if called in defined_functions:
                dot.edge(fn["name"], called)

    dot.render("coderecon_graph", format="png", cleanup=True)

    print("[coderecon] Graph rendered as coderecon_graph.png")
