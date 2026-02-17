import re
from pathlib import Path

# Pre-compiled for speed. Optimized for Rust, TSX, JS, Go, and C-style syntax.
# Also added a group for Python 'def' as a secondary regex fallback.
GENERIC_FUNCTION_RE = re.compile(
    r"(?:async\s+)?(?:fn\s+(\w+)|function\s+(\w+)|(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|const\s+(\w+)\s*:\s*React\.FC|(\w+)\s*\([^)]*\)\s*\{|def\s+(\w+)\s*\()",
    re.MULTILINE
)

# Reserved keywords to ignore during regex discovery
RESERVED = {"if", "for", "while", "switch", "catch", "return", "export", "default"}


def extract_functions(file_path: str, content: str):
    """
    High-speed extraction: AST for Python, Regex for everything else.
    """
    path = Path(file_path)
    functions = []
    suffix = path.suffix.lower()

    # 1. PYTHON AST PARSING (Primary for .py)
    if suffix == ".py":
        import ast
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "path": str(path),
                        "type": "python_ast",
                        "length": len(node.body)  # Real logic density
                    })
            return functions
        except SyntaxError:
            pass  # Fallback to regex if the file is malformed

    # 2. MULTI-LANGUAGE REGEX DISCOVERY (For Rust, JS, TS, Go, and failing Py files)
    # Using finditer is faster as it doesn't build the whole list at once
    for match in GENERIC_FUNCTION_RE.finditer(content):
        # Extract the first non-None group (the function name)
        func_name = next((g for g in match.groups() if g), None)

        if func_name and func_name not in RESERVED:
            functions.append({
                "name": func_name,
                "line": content.count("\n", 0, match.start()) + 1,
                "path": str(path),
                "type": "regex_discovery",
                "length": 0  # Placeholder for regex-found functions
            })

    return functions