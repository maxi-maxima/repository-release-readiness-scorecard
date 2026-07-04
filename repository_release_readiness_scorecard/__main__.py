import argparse, json
from pathlib import Path

CHECKS = [
    ("README.md", 20, "Write a README over 500 characters with install, usage, and examples."),
    ("LICENSE", 15, "Add a LICENSE file so users know how they can reuse the project."),
    (".gitignore", 10, "Add a .gitignore to keep local artifacts out of releases."),
    ("examples", 15, "Include an examples/ directory with runnable sample input or output."),
    ("tests", 20, "Add a tests/ directory with automated checks for the public behavior."),
    ("README.zh-CN.md", 10, "Add README.zh-CN.md to make the project accessible to Chinese readers."),
    ("pyproject.toml", 10, "Add pyproject.toml with package metadata and build configuration."),
]
CHECK_NAMES = [name for name, _, _ in CHECKS]

def score(root):
    root = Path(root)
    checks = []
    total = 0
    for name, points, recommendation in CHECKS:
        exists = (root / name).exists()
        if name == "README.md" and exists:
            exists = len((root / name).read_text(encoding="utf-8", errors="ignore")) > 500
        checks.append({
            "check": name,
            "points": points if exists else 0,
            "max_points": points,
            "passed": exists,
            "recommendation": "" if exists else recommendation,
        })
        total += points if exists else 0
    grade = "ready" if total >= 80 else "needs-work" if total >= 50 else "not-ready"
    return {"score": total, "grade": grade, "checks": checks}

def main(argv=None):
    parser = argparse.ArgumentParser(description="Score repository release readiness")
    parser.add_argument("path", nargs="?", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--min-score", type=int, default=80, help="Minimum score required for a zero exit status")
    parser.add_argument("--require-check", action="append", default=[], choices=CHECK_NAMES, help="Require a specific check to pass even when the total score meets --min-score; may be used multiple times")
    args = parser.parse_args(argv)
    if not 0 <= args.min_score <= 100:
        parser.error("--min-score must be between 0 and 100")
    result = score(args.path)
    failed_required = [check["check"] for check in result["checks"] if check["check"] in args.require_check and not check["passed"]]
    result["required_checks"] = args.require_check
    result["failed_required_checks"] = failed_required
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Score: {result['score']}/100 ({result['grade']})")
        for check in result["checks"]:
            mark = "✓" if check["passed"] else "✗"
            print(f"{mark} {check['check']} {check['points']}/{check['max_points']}")
        if failed_required:
            print(f"Required checks failed: {', '.join(failed_required)}")
    if failed_required:
        return 3
    return 0 if result["score"] >= args.min_score else 2

if __name__ == "__main__":
    raise SystemExit(main())
