import ast


def extract_functions(files):
    functions = []
    for file in files:
        try:
            source = open(file["path"], "r", encoding="utf-8", errors="ignore").read()
            tree = ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):

                line_start = node.lineno
                line_end = getattr(node, "end_lineno", line_start)
                length = line_end - line_start + 1

                called_functions = []

                for inner in ast.walk(node):
                    if isinstance(inner, ast.Call):
                        if isinstance(inner.func, ast.Name):
                            called_functions.append(inner.func.id)

                functions.append({
                    "name": node.name,
                    "path": file["path"],
                    "params": [arg.arg for arg in node.args.args],
                    "line_start": line_start,
                    "line_end": line_end,
                    "length": length,
                    "called_functions": list(set(called_functions)),
                })

    return functions