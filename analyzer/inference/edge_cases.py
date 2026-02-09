import ast

def _emit(fn, inner, case, reason):
    return {
        "function": fn["name"],
        "file": fn["file"],
        "case": case,
        "reason": reason,
        "line": getattr(inner, "lineno", None),
        "node_type": type(inner).__name__,
    }


def detect_edge_cases(functions):
    """
    Infer potential edge cases from control flow and operators
    """
    edge_cases = []

    for fn in functions:
        try:
            source = open(
                fn["file"], "r", encoding="utf-8", errors="ignore"
            ).read()
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == fn["name"]:
                for inner in ast.walk(node):

                    if isinstance(inner, ast.For):
                        edge_cases.append(
                            _emit(
                                fn,
                                inner,
                                "Loop execution",
                                "Loop implies possible empty or large input",
                            )
                        )

                    if isinstance(inner, ast.If):
                        edge_cases.append(
                            _emit(
                                fn,
                                inner,
                                "Conditional branch",
                                "Conditional branches may lead to untested paths",
                            )
                        )

                    if isinstance(inner, ast.While):
                        edge_cases.append(
                            _emit(
                                fn,
                                inner,
                                "While loop",
                                "Loop termination depends on condition",
                            )
                        )

                    if isinstance(inner, ast.Try):
                        edge_cases.append(
                            _emit(
                                fn,
                                inner,
                                "Exception path",
                                "Explicit exception handling present",
                            )
                        )

                    if isinstance(inner, ast.BinOp) and isinstance(inner.op, ast.Div):
                        edge_cases.append(
                            _emit(
                                fn,
                                inner,
                                "Division operation",
                                "Potential division by zero",
                            )
                        )

    return edge_cases
