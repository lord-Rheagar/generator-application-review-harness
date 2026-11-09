# Generator Application Review Harness

Give applications just below a cutoff a second look. The harness finds cases to recheck, verifies that the review cites the original answers, and recalculates the score. It sends cases with missing or invalid evidence to a human reviewer.

This is an independent demo inspired by [Generator Residency](https://generatorresidency.org/). The applications, scores, and rubric are fictional.

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

## Use your own batch

Bring an applications CSV, a first-pass scores CSV, and a rubric. Match the files on application ID. If your export uses different headers, supply a column map. The [input guide](docs/inputs.md) has the required fields and commands for `prepare` and `audit`.

## Verify or rebuild the ZIP

```sh
python -m unittest discover -s tests -v
python scripts/build_skill.py
```

The build writes `dist/review-applications.zip`. The package includes the skill, the harness, and the fictional examples needed to run the demo.
