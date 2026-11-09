"""Command-line entry point for the review harness."""

import argparse
import csv
import json
from pathlib import Path

from .audit import audit_batch, prepare_packet, render_report
from .inputs import load_batch, read_json


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    demo = modes.add_parser("demo", help="Replay the bundled synthetic review")
    demo.add_argument("--batch", action="store_true", help="Use the expanded 16-case synthetic batch")
    for mode in ("prepare", "audit"):
        command = modes.add_parser(mode)
        command.add_argument("--batch", action="store_true", help="Use the expanded 16-case synthetic batch")
        command.add_argument("--applications", type=Path)
        command.add_argument("--scores", type=Path)
        command.add_argument("--rubric", type=Path, default=EXAMPLES / "rubric.json")
        command.add_argument("--mapping", type=Path)
    modes.choices["audit"].add_argument("--findings", type=Path, required=True)
    args = parser.parse_args()
    dataset = EXAMPLES / ("batch" if args.batch else "quick")

    try:
        if args.mode == "demo":
            rubric, cases = load_batch(dataset / "applications.csv", dataset / "first-pass.csv", EXAMPLES / "rubric.json")
            findings = read_json(dataset / "replay-findings.json")
        else:
            rubric, cases = load_batch(
                args.applications or dataset / "applications.csv",
                args.scores or dataset / "first-pass.csv",
                args.rubric,
                args.mapping,
            )
            if args.mode == "prepare":
                print(json.dumps(prepare_packet(rubric, cases), indent=2))
                return
            findings = read_json(args.findings)
        print(render_report(rubric, audit_batch(rubric, cases, findings), replay=args.mode == "demo"))
    except (OSError, csv.Error, ValueError) as exc:
        parser.exit(1, f"Review failed: {exc}\n")


if __name__ == "__main__":
    main()
