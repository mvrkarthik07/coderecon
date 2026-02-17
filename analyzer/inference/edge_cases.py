import ast


def _emit(fn, inner, rule_id, case, reason, severity="low"):
    return {
        "rule_id": rule_id,
        "function": fn["name"],
        "file": fn["path"],
        "case": case,
        "reason": reason,
        "severity": severity,
        "line": getattr(inner, "lineno", None),
        "node_type": type(inner).__name__,
    }


class DepthVisitor(ast.NodeVisitor):
    """Tracks nesting depth of control flow nodes."""

    def __init__(self):
        self.current_depth = 0
        self.max_depth = 0
        self.nesting_nodes = (ast.If, ast.For, ast.While, ast.Try, ast.With)

    def visit_nested(self, node):
        self.current_depth += 1
        self.max_depth = max(self.max_depth, self.current_depth)
        self.generic_visit(node)
        self.current_depth -= 1

    def visit_If(self, node): self.visit_nested(node)

    def visit_For(self, node): self.visit_nested(node)

    def visit_While(self, node): self.visit_nested(node)

    def visit_Try(self, node): self.visit_nested(node)


def detect_edge_cases(functions):
    edge_cases = []

    for fn in functions:
        try:
            with open(fn["path"], "r", encoding="utf-8", errors="ignore") as f:
                tree = ast.parse(f.read())
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == fn["name"]:

                # 1. Check Deep Nesting
                dv = DepthVisitor()
                dv.visit(node)
                if dv.max_depth > 3:
                    edge_cases.append(_emit(
                        fn, node, "CR1001", "Deep Nesting",
                        f"Logic nested {dv.max_depth} levels deep. High cognitive load.", "high"
                    ))

                # 2. Specific Logic Hazards
                for inner in ast.walk(node):
                    if isinstance(inner, (ast.For, ast.While)):
                        edge_cases.append(_emit(
                            fn, inner, "CR2001", "Loop execution",
                            "Potential for infinite loops or O(n) performance hits.", "medium"
                        ))

                    if isinstance(inner, ast.Try):
                        # Check for 'bare' except or too many handlers
                        edge_cases.append(_emit(
                            fn, inner, "CR3001", "Exception path",
                            "Complexity in error recovery paths.", "low"
                        ))

                    if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Div):
                        edge_cases.append(_emit(
                            fn, inner, "CR4001", "Math risk",
                            "Division operation without visible zero-check.", "medium"
                        ))

                    # 3. Detect "God Functions" (Length-based)
                    if hasattr(node, 'end_lineno'):
                        length = node.end_lineno - node.lineno
                        if length > 50:
                            edge_cases.append(_emit(
                                fn, node, "CR1002", "Large Function",
                                f"Function is {length} lines long. Suggest refactoring.", "medium"
                            ))

    return edge_cases