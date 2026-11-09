"""Check first-pass application scores against a second review's evidence."""

import argparse
from collections import Counter
import csv
import json
from pathlib import Path


ASSETS = Path(__file__).resolve().parents[1] / "assets"
CRITERIA = ("execution", "gap_judgment", "initiative", "commitment")
EVIDENCE_FIELDS = ("execution_summary", "work_example")
APPLICATION_FIELDS = ("application_id", "name", "track", *EVIDENCE_FIELDS)
SCORE_FIELDS = ("application_id", *CRITERIA, "execution_reason")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_rubric(path):
    rubric = read_json(path)
    if not isinstance(rubric, dict):
        raise ValueError("The rubric must be a JSON object.")
    version = rubric.get("version")
    cutoff = rubric.get("cutoff")
    band = rubric.get("audit_band")
    weights = rubric.get("weights")
    anchors = rubric.get("execution_anchors")
    if not isinstance(version, str) or not version.strip():
        raise ValueError("The rubric needs a version.")
    if type(cutoff) is not int or not 1 <= cutoff <= 100:
        raise ValueError("The rubric cutoff must be an integer from 1 to 100.")
    if type(band) is not int or not 1 <= band <= cutoff:
        raise ValueError("The audit band must be a positive integer at most the cutoff.")
    if (not isinstance(weights, dict) or set(weights) != set(CRITERIA)
            or any(type(value) is not int or value <= 0 for value in weights.values())
            or sum(weights.values()) != 100):
        raise ValueError("The four rubric weights must be positive integers totaling 100.")
    if (not isinstance(anchors, dict) or set(anchors) != set("012345")
            or any(not isinstance(value, str) or not value.strip() for value in anchors.values())):
        raise ValueError("The rubric needs execution anchors for scores 0 through 5.")
    return rubric


def load_rows(path, fields, column_map):
    if not isinstance(column_map, dict) or set(column_map) - set(fields):
        raise ValueError(f"{path.name} has an invalid column mapping.")
    columns = {field: column_map.get(field, field) for field in fields}
    if any(not isinstance(header, str) or not header for header in columns.values()):
        raise ValueError(f"{path.name} column names must be nonempty strings.")
    if len(set(columns.values())) != len(fields):
        raise ValueError(f"{path.name} maps multiple fields to the same column.")

    rows = {}
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers):
            raise ValueError(f"{path.name} has duplicate column headers.")
        missing = set(columns.values()) - set(headers)
        if missing:
            raise ValueError(f"{path.name} is missing columns: {', '.join(sorted(missing))}.")
        for raw in reader:
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(f"{path.name} has an incomplete or extra field on line {reader.line_num}.")
            row = {field: raw[header] for field, header in columns.items()}
            application_id = row["application_id"].strip()
            if not application_id or application_id in rows:
                raise ValueError(f"{path.name} has a blank or duplicate ID on line {reader.line_num}.")
            row["application_id"] = application_id
            rows[application_id] = row
    if not rows:
        raise ValueError(f"{path.name} contains no rows.")
    return rows


def weighted_score(scores, rubric):
    return sum(scores[key] * rubric["weights"][key] for key in CRITERIA) / 5


def load_batch(applications_path, scores_path, rubric_path, mapping_path=None):
    rubric = load_rubric(rubric_path)
    mapping = read_json(mapping_path) if mapping_path else {}
    if not isinstance(mapping, dict) or set(mapping) - {"applications", "first_pass"}:
        raise ValueError("Column mapping keys must be applications or first_pass.")
    applications = load_rows(applications_path, APPLICATION_FIELDS, mapping.get("applications", {}))
    first_pass = load_rows(scores_path, SCORE_FIELDS, mapping.get("first_pass", {}))
    if applications.keys() != first_pass.keys():
        raise ValueError("Applications and first-pass scores must contain the same application IDs.")

    cases = []
    for application_id, application in applications.items():
        baseline = first_pass[application_id]
        scores = {}
        for criterion in CRITERIA:
            value = baseline[criterion].strip()
            if value not in {"0", "1", "2", "3", "4", "5"}:
                raise ValueError(f"{application_id} needs a 0–5 integer score for {criterion}.")
            scores[criterion] = int(value)
        total = weighted_score(scores, rubric)
        cases.append({
            **application,
            "scores": scores,
            "first_pass_reason": baseline["execution_reason"],
            "first_pass_total": total,
            "in_audit_band": rubric["cutoff"] - rubric["audit_band"] <= total < rubric["cutoff"],
        })
    return rubric, cases


def prepare_packet(rubric, cases):
    return {
        "rubric_version": rubric["version"],
        "execution_anchors": rubric["execution_anchors"],
        "cases": [
            {key: case[key] for key in ("application_id", *EVIDENCE_FIELDS)}
            for case in cases if case["in_audit_band"]
        ],
    }


def index_findings(findings, cases):
    if not isinstance(findings, list):
        raise ValueError("Second-pass findings must be a JSON array.")
    audited_ids = {case["application_id"] for case in cases if case["in_audit_band"]}
    by_id = {}
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("Each second-pass finding must be an object.")
        application_id = finding.get("application_id")
        if not isinstance(application_id, str) or application_id not in audited_ids:
            raise ValueError("Second-pass findings may only reference IDs in the audit packet.")
        if application_id in by_id:
            raise ValueError(f"Multiple second-pass findings for {application_id}.")
        by_id[application_id] = finding
    return by_id


def evidence_is_valid(case, finding):
    score = finding.get("execution_score")
    field = finding.get("field")
    quote = finding.get("quote")
    reason = finding.get("reason")
    return (
        type(score) is int and 0 <= score <= 5
        and field in EVIDENCE_FIELDS
        and isinstance(quote, str) and len(quote.strip()) >= 15 and quote in case[field]
        and isinstance(reason, str) and bool(reason.strip())
    )


def audit_batch(rubric, cases, findings):
    by_id = index_findings(findings, cases)
    results = []
    for case in cases:
        result = {"case": case, "status": "Outside audit band"}
        if case["in_audit_band"]:
            finding = by_id.get(case["application_id"], {})
            if evidence_is_valid(case, finding):
                updated_scores = {**case["scores"], "execution": finding["execution_score"]}
                proposed = weighted_score(updated_scores, rubric)
                status = "Flag for work-test review" if proposed >= rubric["cutoff"] else "Stays below cutoff"
                result.update(status=status, proposed_total=proposed, finding=finding)
            else:
                result["status"] = "Needs human review (missing or invalid evidence)"
        results.append(result)
    return results


def render_report(rubric, results, replay):
    cutoff = rubric["cutoff"]
    lower = cutoff - rubric["audit_band"]
    lines = ["# Generator application review", ""]
    if replay:
        lines.extend(["Synthetic demo using a staged first pass and recorded second-pass findings.", ""])
    lines.extend([
        f"Rubric {rubric['version']} · work-test cutoff {cutoff}/100 · audit band [{lower}, {cutoff})",
        "Recommendations are for reviewer confirmation.",
        "", f"## Summary ({len(results)} applications)",
    ])
    counts = Counter(result["status"] for result in results)
    lines.extend(f"- {count} × {status}" for status, count in counts.items())
    for result in results:
        case = result["case"]
        lines.extend([
            "", f"## {case['application_id']} — {case['name']} ({case['track']})",
            f"First pass: {case['first_pass_total']:g}/100. {result['status']}.",
        ])
        if "finding" in result:
            finding = result["finding"]
            lines.extend([
                f"Execution: {case['scores']['execution']}/5 → {finding['execution_score']}/5.",
                f"Proposed total: {result['proposed_total']:g}/100.",
                f"First-pass rationale: {case['first_pass_reason']}",
                f"Verified source quote ({finding['field']}): {finding['quote']}",
                f"Second-pass rationale: {finding['reason']}",
            ])
    return "\n".join(lines)


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
        command.add_argument("--rubric", type=Path, default=ASSETS / "rubric.json")
        command.add_argument("--mapping", type=Path)
    modes.choices["audit"].add_argument("--findings", type=Path, required=True)
    args = parser.parse_args()
    dataset = ASSETS / "batch" if args.batch else ASSETS

    try:
        if args.mode == "demo":
            rubric, cases = load_batch(dataset / "applications.csv", dataset / "first-pass.csv", ASSETS / "rubric.json")
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
