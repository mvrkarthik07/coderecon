from pathlib import Path


def write_markdown(path: str, content: str):
    out_dir = Path(".coderecon/reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = path.replace("/", "_").replace("\\", "_")
    out_file = out_dir / f"{safe_name}.md"

    out_file.write_text(content, encoding="utf-8")
    return out_file
