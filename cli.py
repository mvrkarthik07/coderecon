from pathlib import Path
import json
import argparse

from analyzer.scan import run_analysis


def main():
    parser = argparse.ArgumentParser(
        prog="coderecon",
        description="Deterministic codebase reconnaissance"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a codebase")
    analyze.add_argument("path", help="Path to codebase")

    args = parser.parse_args()

    if args.command == "analyze":
        run_analyze(args.path)


def run_analyze(path: str):
    analysis = run_analysis(path)

    out = Path(".coderecon")
    out.mkdir(exist_ok=True)

    output_path = out / "analysis.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)

    print("[coderecon] Scan complete")
    print(f"[coderecon] Files scanned: {len(analysis['files'])}")
    print(f"[coderecon] Functions detected: {len(analysis['functions'])}")
    print(f"[coderecon] Tests detected: {len(analysis['tests'])}")
    print(f"[coderecon] Edge cases inferred: {len(analysis['edge_cases'])}")
    print(f"[coderecon] Signals generated: {len(analysis['signals'])}")
    print(f"[coderecon] Analysis written to {output_path}")


if __name__ == "__main__":
    main()
