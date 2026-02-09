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
                functions.append({
                    "name": node.name,
                    "path": file["path"],
                    "params": [arg.arg for arg in node.args.args],
                    "line_start": node.lineno,
                    "branches": sum(isinstance(n,ast.If) for n in ast.walk(node)),
                    "has_try_except": any(isinstance(n,ast.Try) for n in ast.walk(node)),
                })
    return functions