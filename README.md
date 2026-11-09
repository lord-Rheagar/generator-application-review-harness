# Generator Application Review Harness

Give applications just below a cutoff a second look. The harness finds cases to recheck, verifies that the review cites the original answers, and recalculates the score. It sends cases with missing or invalid evidence to a human reviewer.

This is an independent demo inspired by [Generator Residency](https://generatorresidency.org/). The applications, scores, and rubric are fictional.

Already have an export? Go straight to [Run it on your applications](#run-it-on-your-applications).

## See it work

Mara Vale scored **68/100**, below the demo cutoff of **70**. The first pass credited her with helping start a pilot. Her other answer describes owning its delivery:

> I recruited six reviewers, wrote the rubric, and ran two rounds of a pilot that processed 48 submissions.

The harness verifies the excerpt against her answer, calculates a proposed score of **84/100**, and flags her for **work-test review**. A human reviewer decides whether to advance her.

## Quick start

Clone the repository and run the demo with Python 3.9 or newer. The replay uses Python's standard library and the bundled data.

```sh
git clone https://github.com/lord-Rheagar/generator-application-review-harness.git
cd generator-application-review-harness
python -X utf8 -m review_harness demo
```

Add `--batch` to run the [16-case example](examples/batch/). It flags three applications, routes three evidence problems to a human, and shows which cases fall outside the review band.

### Claude Code

Start `claude` from the repository root. Run one of these commands in the Claude Code session:

| Command | What it does |
| --- | --- |
| `/review-applications demo` | Replays the four-case example, including Mara's application. |
| `/review-applications batch-demo` | Replays the 16-case example. |
| `/review-applications live-batch` | Asks Claude to review the borderline cases and passes its findings to the verifier. |

The replays use staged first-pass scores and recorded findings. A fresh review generates new findings and may give different scores.

### Claude chat

Download [review-applications.zip](https://github.com/lord-Rheagar/generator-application-review-harness/releases/latest/download/review-applications.zip) and upload it under **Customize → Skills**. With custom skills and code execution enabled, ask Claude to **run the review-applications demo and show the flagged applicant**. [Claude skill upload guide](https://support.claude.com/en/articles/12512180-use-skills-in-claude)

## Run it on your applications

### 1. Prepare three files

Create a `review-data` folder **next to** the cloned repository. Put the following files there. Use a workspace and model your team has approved for applicant data. A display ID works in the `name` column when the reviewer does not need the applicant's name.

| File | What to put in it |
| --- | --- |
| `applications.csv` | One row per application with `application_id`, `name`, `track`, `execution_summary`, and `work_example`. Use the original answer text in the last two columns. [Example CSV](examples/quick/applications.csv) |
| `first-pass.csv` | One row per application with `application_id`, `execution`, `gap_judgment`, `initiative`, `commitment`, and `execution_reason`. The four scores must be integers from 0 to 5. [Example scores](examples/quick/first-pass.csv) |
| `rubric.json` | Start from the [sample rubric](examples/rubric.json). Set your version, cutoff, audit band, four weights totaling 100, and execution anchors for scores 0 through 5. |

Use the same unique application IDs in both CSVs. The harness needs a first-pass score for each application. Export those scores from your existing process, or have reviewers score the applications first. If your export uses different headers, rename the columns or create a [`mapping.json`](docs/inputs.md#map-your-column-names).

If your form has only one answer about execution, put it in `work_example` and leave `execution_summary` blank. If your program has one track, use the same label in every `track` cell.

### 2. Run a fresh review

**With Claude Code**, start from the repository root and grant access to the data folder:

```sh
claude --add-dir ../review-data
```

Paste this into the Claude Code session:

```text
/review-applications Run a fresh review using ../review-data/applications.csv, first-pass scores in ../review-data/first-pass.csv, and the rubric in ../review-data/rubric.json. Run prepare and audit on these files. Save the audit report to ../review-data/review-report.md.
```

If you made a column map, add `Use ../review-data/mapping.json for both commands` to the request. If you use the **uploaded Claude skill**, attach the approved files and ask for the same fresh review using the attachment names. Ask for the report as a downloadable Markdown file.

**With the terminal and a separate reviewer**, run these commands from the repository root. First, generate the review packet:

```sh
python -X utf8 -m review_harness prepare --applications ../review-data/applications.csv --scores ../review-data/first-pass.csv --rubric ../review-data/rubric.json
```

Give the printed packet to a human reviewer or an approved model. Have them score execution using the anchors and save their findings as `../review-data/findings.json`. Each finding needs an `application_id`, an integer `execution_score` from 0 to 5, the source `field` (`execution_summary` or `work_example`), an exact `quote` of at least 15 characters, and a short `reason`. Use the [example findings](examples/quick/replay-findings.json) for the JSON format. Leave out cases where the reviewer cannot cite evidence.

Run the verifier with the same input files:

```sh
python -X utf8 -m review_harness audit --applications ../review-data/applications.csv --scores ../review-data/first-pass.csv --rubric ../review-data/rubric.json --findings ../review-data/findings.json
```

If using a column map, add `--mapping ../review-data/mapping.json` to both commands.

### 3. Read the report and decide

| Result | What to do |
| --- | --- |
| **Flag for work-test review** | Check the cited answer and proposed score before deciding whether to advance the applicant. |
| **Needs human review** | Look at the original application. The second review's evidence is missing or failed verification. |
| **Stays below cutoff** | The verified review kept the proposed total below your cutoff. |
| **Outside audit band** | The first-pass score was at or above the cutoff, or too far below it for this run. |

The report proposes changes to the **execution** score. Your team makes the final decision on each application.

## How it works

1. **Select cases.** `prepare` joins applications to first-pass scores and selects the band just below the cutoff. With a cutoff of 70 and a band of 5, that means 65 up to but below 70.
2. **Review the answers.** Claude receives the two execution answers and the rubric anchors for each case in the band. The packet withholds the first-pass scores. The reviewer proposes an execution score, cites an exact excerpt, and gives a reason.
3. **Check the evidence and recalculate.** `audit` checks that the excerpt exists in the named answer. It uses the rubric weights to recompute the total and flags cases that cross the cutoff. A missing, fabricated, or misattributed excerpt goes to human review.

The second pass rechecks **execution** and carries the other criterion scores through. Quote verification confirms what the applicant wrote. Human reviewers judge the underlying claims and make decisions.

## Find your way around

| Path | What’s inside |
| --- | --- |
| [`review_harness/`](review_harness/) | Python CLI, input validation, scoring, and reporting. |
| [`examples/`](examples/) | Two fictional batches, a sample rubric, and recorded review findings. |
| [`.claude/skills/review-applications/`](.claude/skills/review-applications/) | Instructions that connect Claude to the same Python harness. |
| [`docs/inputs.md`](docs/inputs.md) | CSV and JSON formats, column mapping, and commands for a custom batch. |
| [`tests/`](tests/) | Checks for the replays, input handling, and the standalone ZIP. |
| [`scripts/build_skill.py`](scripts/build_skill.py) | Builds the uploadable ZIP from the public source files. |

## Verify or rebuild the ZIP

```sh
python -m unittest discover -s tests -v
python scripts/build_skill.py
```

The build writes `dist/review-applications.zip`. The package includes the skill, the harness, and the fictional examples needed to run the demo.
