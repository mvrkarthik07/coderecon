from pathlib import Path
import ast

def map_tests(files):
    """
    Discover test functions and infer which priduction functions they reference.
    """
    tests=[]

    for file in files:
        path = Path(file["path"])

        if not (
            path.name.startswith("test_") or "test" in path.parts
        ):
            continue

        try:
            source = open(path, "r",encdoing="utf-8",errors="ignore").read()
            tree= ast.parse(source)
        except Exception:
            continue

        for node in ast.walk(tree):
            if isinstance(node,ast.FunctionDef) and node.name.startswith("test_"):
                referenced = set()

                for inner in ast.walk(node):
                    if isinstance(inner,ast.Call):
                        if isinstance(inner.func,ast.Name):
                            referenced.add(inner.func.id)

                tests.append({
                    "test_name": node.name,
                    "file":str(path),
                    "references":sorted(referenced)
                })
                

