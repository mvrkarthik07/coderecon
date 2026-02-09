from pathlib import Path

SUPPORTED_EXTENSIONS = {'.py', '.java', '.js','.ts', '.go', '.rb', '.php', '.cpp', '.c', '.cs', '.swift', '.kt', '.rs', '.m', '.scala', '.pl', '.sh', '.html', '.css', '.xml', '.json', '.yml', '.yaml', 'jsx', 'tsx'}

def discover_files(root_path: str):
    """
    Walk the file system and return all supported source files.
    No Assumptions,no filtering beyond extensions.
    """
    root  = Path(root_path)
    files = []
    if not root.exists():
        return files
    
    for path in root.rglob('*'):
        if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
            try:
                loc = sum(1 for _ in path.open('r', encoding='utf-8', errors='ignore'))
            except Exception:
                loc = 0

            files.append({
                "path": str(path),
                "extension": path.suffix,
                "loc":loc
            })
    return files