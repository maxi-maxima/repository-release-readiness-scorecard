import argparse, fnmatch, json
from urllib.parse import quote
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


def load_ignore_patterns(root):
    gitignore = Path(root) / ".gitignore"
    if not gitignore.exists():
        return []
    patterns = []
    for line in gitignore.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("!"):
            patterns.append(line.rstrip("/"))
    return patterns


def is_ignored(relative_path, patterns):
    normalized = relative_path.as_posix()
    parts = relative_path.parts
    for pattern in patterns:
        cleaned = pattern.lstrip("/")
        if fnmatch.fnmatch(normalized, cleaned) or fnmatch.fnmatch(relative_path.name, cleaned):
            return True
        if cleaned in parts:
            return True
    return False


def inventory_untracked_artifacts(root):
    root = Path(root)
    patterns = load_ignore_patterns(root)
    findings = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if ".git" in rel.parts:
            continue
        if is_ignored(rel, patterns):
            continue
        if any(part in {"__pycache__", ".pytest_cache", "node_modules", "dist", "build"} for part in rel.parts):
            findings.append(rel.as_posix())
        elif path.suffix in {".pyc", ".pyo", ".log", ".tmp", ".bak"}:
            findings.append(rel.as_posix())
    return findings


def score(root, *, ignored_checks=(), include_artifact_check=False):
    root = Path(root)
    ignored_checks = set(ignored_checks)
    checks = []
    total = 0
    max_score = 0
    for name, points, recommendation in CHECKS:
        if name in ignored_checks:
            continue
        max_score += points
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
    score_percent = round((total / max_score) * 100) if max_score else 0
    grade = "ready" if score_percent >= 80 else "needs-work" if score_percent >= 50 else "not-ready"
    result = {"score": total, "max_score": max_score, "score_percent": score_percent, "grade": grade, "checks": checks, "ignored_checks": sorted(ignored_checks)}
    if include_artifact_check:
        artifacts = inventory_untracked_artifacts(root)
        result["artifact_findings"] = artifacts
        result["artifact_check_passed"] = not artifacts
    return result


def format_markdown(result):
    lines = [
        "## Release Readiness Score",
        "",
        f"**Score:** {result['score']}/{result.get('max_score', 100)} ({result['score_percent']}%, {result['grade']})",
        "",
        "| Check | Result | Points | Recommendation |",
        "| --- | --- | --- | --- |",
    ]
    for check in result["checks"]:
        result_text = "pass" if check["passed"] else "fail"
        lines.append(f"| {check['check']} | {result_text} | {check['points']}/{check['max_points']} | {check['recommendation']} |")
    if "artifact_findings" in result:
        artifact_result = "pass" if result["artifact_check_passed"] else "fail"
        recommendation = "" if result["artifact_check_passed"] else "Ignore or remove generated artifacts before release."
        lines.append(f"| generated artifacts | {artifact_result} | 0/0 | {recommendation} |")
    if result.get("ignored_checks"):
        lines.extend(["", f"Ignored checks: {', '.join(result['ignored_checks'])}"])
    if result["failed_required_checks"]:
        lines.extend(["", f"Required checks failed: {', '.join(result['failed_required_checks'])}"])
    return "\n".join(lines)


def format_sarif(result, root):
    root_uri = Path(root).resolve().as_uri() + "/"
    rules = []
    results = []
    for check in result["checks"]:
        rule_id = f"release-readiness/{check['check']}"
        rules.append({
            "id": rule_id,
            "name": check["check"],
            "shortDescription": {"text": f"{check['check']} release-readiness check"},
            "help": {"text": check["recommendation"] or "Release-readiness check passed."},
            "properties": {"max_points": check["max_points"]},
        })
        if not check["passed"]:
            results.append({
                "ruleId": rule_id,
                "level": "error" if check["check"] in result.get("required_checks", []) else "warning",
                "message": {"text": check["recommendation"]},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": quote(check["check"]), "uriBaseId": "REPO_ROOT"}
                    }
                }],
                "properties": {"points": check["points"], "max_points": check["max_points"]},
            })
    if "artifact_findings" in result:
        rule_id = "release-readiness/generated-artifacts"
        rules.append({
            "id": rule_id,
            "name": "generated artifacts",
            "shortDescription": {"text": "Generated artifacts should be ignored or removed before release"},
            "help": {"text": "Ignore or remove generated artifacts before release."},
        })
        for artifact in result["artifact_findings"]:
            results.append({
                "ruleId": rule_id,
                "level": "error",
                "message": {"text": "Generated artifact is not covered by .gitignore."},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": quote(artifact), "uriBaseId": "REPO_ROOT"}
                    }
                }],
            })
    payload = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "repository-release-readiness-scorecard",
                    "informationUri": "https://github.com/maxi-maxima/repository-release-readiness-scorecard",
                    "rules": rules,
                }
            },
            "originalUriBaseIds": {"REPO_ROOT": {"uri": root_uri}},
            "properties": {
                "score": result["score"],
                "max_score": result["max_score"],
                "score_percent": result["score_percent"],
                "grade": result["grade"],
            },
            "results": results,
        }],
    }
    return json.dumps(payload, indent=2)


def render_output(result, *, as_json=False, as_markdown=False, as_sarif=False, root='.'):
    if as_json:
        return json.dumps(result, indent=2)
    if as_sarif:
        return format_sarif(result, root)
    if as_markdown:
        return format_markdown(result)
    lines = [f"Score: {result['score']}/{result.get('max_score', 100)} ({result['score_percent']}%, {result['grade']})"]
    for check in result["checks"]:
        mark = "✓" if check["passed"] else "✗"
        lines.append(f"{mark} {check['check']} {check['points']}/{check['max_points']}")
    if "artifact_findings" in result:
        mark = "✓" if result["artifact_check_passed"] else "✗"
        lines.append(f"{mark} generated artifacts {len(result['artifact_findings'])} finding(s)")
        for artifact in result["artifact_findings"][:5]:
            lines.append(f"  - {artifact}")
    if result.get("ignored_checks"):
        lines.append(f"Ignored checks: {', '.join(result['ignored_checks'])}")
    if result["failed_required_checks"]:
        lines.append(f"Required checks failed: {', '.join(result['failed_required_checks'])}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score repository release readiness")
    parser.add_argument("path", nargs="?", default=".")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument("--json", action="store_true")
    output_group.add_argument("--markdown", action="store_true", help="Print a Markdown summary suitable for PR comments or issue reports")
    output_group.add_argument("--sarif", action="store_true", help="Print a SARIF 2.1.0 report suitable for GitHub code scanning uploads")
    parser.add_argument("--output", help="Write the rendered report to this file as well as stdout")
    parser.add_argument("--min-score", type=int, default=80, help="Minimum score required for a zero exit status")
    parser.add_argument("--require-check", action="append", default=[], choices=CHECK_NAMES, help="Require a specific check to pass even when the total score meets --min-score; may be used multiple times")
    parser.add_argument("--ignore-check", action="append", default=[], choices=CHECK_NAMES, help="Exclude a check from scoring for repositories where that artifact is intentionally not applicable; may be used multiple times")
    parser.add_argument("--artifact-check", action="store_true", help="Report generated or cache artifacts that are not covered by .gitignore")
    parser.add_argument("--fail-on-artifacts", action="store_true", help="Return a non-zero status when --artifact-check finds generated artifacts")
    args = parser.parse_args(argv)
    if not 0 <= args.min_score <= 100:
        parser.error("--min-score must be between 0 and 100")
    ignored = set(args.ignore_check)
    required = [name for name in args.require_check if name not in ignored]
    result = score(args.path, ignored_checks=ignored, include_artifact_check=args.artifact_check or args.fail_on_artifacts)
    failed_required = [check["check"] for check in result["checks"] if check["check"] in required and not check["passed"]]
    result["required_checks"] = required
    result["failed_required_checks"] = failed_required
    output = render_output(result, as_json=args.json, as_markdown=args.markdown, as_sarif=args.sarif, root=args.path)
    print(output)
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    if failed_required:
        return 3
    if args.fail_on_artifacts and not result.get("artifact_check_passed", True):
        return 4
    return 0 if result["score_percent"] >= args.min_score else 2


if __name__ == "__main__":
    raise SystemExit(main())
