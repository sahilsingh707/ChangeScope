import argparse
import json
from dataclasses import asdict
from pathlib import Path

from changescope.impact_report import analyze_repository


def main() -> None:
    parser = argparse.ArgumentParser(prog="changescope")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("--repo", type=Path, default=Path.cwd())
    report_parser.add_argument("--base", required=True)
    report_parser.add_argument("--target", default="HEAD")
    report_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "report":
        report = analyze_repository(args.repo, args.base, args.target)
        data = asdict(report)

        if args.json:
            print(json.dumps(data, indent=2))
            return

        print("ChangeScope Impact Report")
        print("=========================")
        print("Changed functions:")
        for identifier in report.changed_function_ids:
            print(f"  - {identifier}")

        print("\nPotentially affected functions:")
        for identifier in report.affected_function_ids:
            print(f"  - {identifier}")

        print("\nRecommended tests:")
        for test_file in report.recommended_tests:
            print(f"  - {test_file}")


if __name__ == "__main__":
    main()
