"""Load and validate application exports, scores, and rubrics."""

import csv
import json

from .audit import CRITERIA, EVIDENCE_FIELDS, weighted_score


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
