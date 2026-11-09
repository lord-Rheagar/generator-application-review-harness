import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from zipfile import ZipFile

from scripts.build_skill import build_skill


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def run_harness(*args, cwd=ROOT):
    return subprocess.run(
        [sys.executable, "-X", "utf8", "-m", "review_harness", *args],
        cwd=cwd, check=True, capture_output=True, encoding="utf-8",
    ).stdout


class HarnessTests(unittest.TestCase):
    def test_quick_demo_surfaces_the_missed_application(self):
        report = run_harness("demo")
        self.assertIn("First pass: 68/100. Flag for work-test review.", report)
        self.assertIn("Proposed total: 84/100.", report)
        self.assertIn("I recruited six reviewers, wrote the rubric", report)
        self.assertIn("First pass: 67/100. Stays below cutoff.", report)

    def test_batch_demo_reports_all_four_outcomes(self):
        report = run_harness("demo", "--batch")
        self.assertIn("Summary (16 applications)", report)
        self.assertIn("3 × Flag for work-test review", report)
        self.assertIn("5 × Stays below cutoff", report)
        self.assertIn("3 × Needs human review", report)
        self.assertIn("5 × Outside audit band", report)

    def test_prepare_passes_only_borderline_cases_and_source_answers(self):
        packet = json.loads(run_harness("prepare", "--batch"))
        ids = {case["application_id"] for case in packet["cases"]}
        self.assertEqual(len(ids), 11)
        self.assertNotIn("B-112", ids)  # At the cutoff.
        self.assertNotIn("B-114", ids)  # Below the audit band.
        for case in packet["cases"]:
            self.assertEqual(set(case), {"application_id", "execution_summary", "work_example"})

    def test_audit_uses_supplied_files_and_rejects_fabricated_quote(self):
        applications = EXAMPLES / "quick" / "applications.csv"
        scores = EXAMPLES / "quick" / "first-pass.csv"
        rubric = EXAMPLES / "rubric.json"
        findings = json.loads((EXAMPLES / "quick" / "replay-findings.json").read_text(encoding="utf-8"))
        findings[0]["quote"] = "I ran a completely different fictional pilot."
        with TemporaryDirectory() as temp:
            path = Path(temp) / "findings.json"
            path.write_text(json.dumps(findings), encoding="utf-8")
            report = run_harness(
                "audit", "--applications", str(applications), "--scores", str(scores),
                "--rubric", str(rubric), "--findings", str(path),
            )
        self.assertIn("First pass: 68/100. Needs human review", report)
        self.assertNotIn("Proposed total: 84/100.", report)

    def test_skill_zip_runs_the_same_commands_outside_the_checkout(self):
        with TemporaryDirectory() as temp:
            folder = Path(temp)
            package = folder / "review-applications.zip"
            build_skill(package)
            with ZipFile(package) as archive:
                self.assertIsNone(archive.testzip())
                self.assertEqual({name.split("/")[0] for name in archive.namelist()}, {"review-applications"})
                archive.extractall(folder)
            skill = folder / "review-applications"
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertTrue((skill / "docs" / "inputs.md").is_file())
            for args in (("demo",), ("demo", "--batch"), ("prepare", "--batch")):
                self.assertEqual(run_harness(*args, cwd=skill), run_harness(*args))


if __name__ == "__main__":
    unittest.main()
