"""Package the same harness used by the checkout as a Claude skill ZIP."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "review-applications"
SKILL_ENTRY = ROOT / ".claude" / "skills" / SKILL_NAME / "SKILL.md"
PACKAGE_FILES = (
    "review_harness/__init__.py",
    "review_harness/__main__.py",
    "review_harness/audit.py",
    "review_harness/inputs.py",
    "docs/inputs.md",
    "examples/rubric.json",
    *(f"examples/{batch}/{name}" for batch in ("quick", "batch")
      for name in ("applications.csv", "first-pass.csv", "replay-findings.json")),
)


def build_skill(destination):
    contents = [("SKILL.md", SKILL_ENTRY.read_bytes())]
    contents.extend((name, (ROOT / name).read_bytes()) for name in PACKAGE_FILES)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, "w") as archive:
        for name, content in contents:
            archive.writestr(ZipInfo(f"{SKILL_NAME}/{name}"), content, compress_type=ZIP_DEFLATED)


if __name__ == "__main__":
    output = ROOT / "dist" / f"{SKILL_NAME}.zip"
    build_skill(output)
    print(output)
