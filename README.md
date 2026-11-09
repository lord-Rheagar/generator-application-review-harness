# Generator Application Review Harness

Review applications just below a cutoff. The harness checks a second review against the original answers and flags applicants whose updated scores merit a human look.

This is an independent demo inspired by [Generator Residency](https://generatorresidency.org/). All applicants, scores, and rubric settings are fictional.

## Try it in Claude Code

Install Python 3.9 or later, then clone the repo and open it in Claude Code.

```sh
git clone https://github.com/lord-Rheagar/generator-application-review-harness.git
cd generator-application-review-harness
claude
```

Run `/review-applications demo` for four cases or `/review-applications batch-demo` for 16 cases. The demos replay recorded findings. Use `/review-applications live-batch` for a fresh Claude review.

## Try it in Claude chat

1. Download [review-applications.zip](https://github.com/lord-Rheagar/generator-application-review-harness/releases/latest/download/review-applications.zip).
2. In Claude, go to **Customize → Skills** and upload the ZIP. Your workspace needs custom skills and code execution enabled.
3. Ask Claude to **run the review-applications demo and show the flagged applicant**.

## What you’ll see

Mara Vale scored **68** against a cutoff of **70**. Her first answer said she helped start a pilot. Another answer described recruiting six reviewers, writing the rubric, and running two rounds that processed 48 submissions.

The harness verifies that evidence appears in her application, recalculates her proposed score at **84**, and flags her for work-test review. A human decides whether to advance her.

## Run it from a terminal

```sh
python -X utf8 .claude/skills/review-applications/scripts/review.py demo --batch
```

To use another batch, see the [input guide](.claude/skills/review-applications/references/inputs.md) for the application CSV, first-pass scores, rubric, and column mapping.
