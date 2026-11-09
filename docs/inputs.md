# Review your own CSV export

## Files to prepare

| File | Required fields |
| --- | --- |
| Application CSV | `application_id`, `name`, `track`, `execution_summary`, `work_example` |
| First-pass score CSV | `application_id`, `execution`, `gap_judgment`, `initiative`, `commitment`, `execution_reason` |
| Rubric JSON | `version`, `cutoff`, `audit_band`, `weights`, `execution_anchors` |

Both CSVs need one row per application and the same set of IDs. Scores are integers from 0 to 5. Extra named columns are ignored. Use a display ID in the `name` column if you only need to identify the case. See the [four-case example](../examples/quick/) and [sample rubric](../examples/rubric.json).

The rubric's four weights total 100. Its cutoff and audit band are points on that 100-point scale. The lower edge of the band is included and the cutoff itself is excluded. A cutoff of 70 with a band of 5 audits scores from 65 up to 70. This harness rechecks execution and carries the other three scores through from the first pass.

## Map your column names

For different export headers, pass `--mapping mapping.json` to both `prepare` and `audit`. Map each canonical field to the actual CSV header. Fields omitted from the mapping keep their canonical names.

```json
{
  "applications": {
    "application_id": "Response ID",
    "work_example": "Tell us what you delivered"
  },
  "first_pass": {
    "application_id": "Response ID",
    "execution": "Execution score"
  }
}
```

## Prepare and audit

Use a rubric and data source your review team has approved. Keep real exports outside this repository. From the repository root, create a packet for a second reviewer:

```sh
python -X utf8 -m review_harness prepare --applications /path/to/applications.csv --scores /path/to/first-pass.csv --rubric /path/to/rubric.json
```

The packet contains the IDs and two execution answers for cases in the band, plus the rubric anchors. The reviewer returns a JSON array. Each finding gives `application_id`, integer `execution_score` from 0 to 5, `field` (`execution_summary` or `work_example`), an exact `quote` from that field, and a short `reason`. See [recorded findings](../examples/quick/replay-findings.json) for an example. Save the array and run:

```sh
python -X utf8 -m review_harness audit --applications /path/to/applications.csv --scores /path/to/first-pass.csv --rubric /path/to/rubric.json --findings /path/to/findings.json
```

Use the same input files and mapping in both commands. The report lists each case's first-pass score, the proposed score if the excerpt passes validation, and its review status. A verified excerpt establishes what the applicant wrote. A human reviewer decides how much weight the evidence deserves.
