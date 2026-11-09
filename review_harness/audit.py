"""Prepare an independent review and verify its proposed scores."""

from collections import Counter


CRITERIA = ("execution", "gap_judgment", "initiative", "commitment")
EVIDENCE_FIELDS = ("execution_summary", "work_example")


def weighted_score(scores, rubric):
    return sum(scores[key] * rubric["weights"][key] for key in CRITERIA) / 5


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
