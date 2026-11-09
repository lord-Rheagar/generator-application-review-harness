# Inputs for a fresh review

The application CSV contains `application_id`, `name`, `track`, `execution_summary`, and `work_example`. The first-pass CSV contains `application_id`, `execution`, `gap_judgment`, `initiative`, `commitment`, and `execution_reason`. Scores are integers from 0 to 5. Both files use the same set of stable application IDs, with one row per ID. Extra named columns are ignored. The `name` column may use a display ID in place of a name.

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

Pass a team-approved rubric with `--rubric`. Follow the structure of [the example rubric](../assets/rubric.json). Weights total 100. The cutoff and audit band are points on the 100-point weighted scale. This demo audits execution and carries the other criterion scores through from the first pass.
