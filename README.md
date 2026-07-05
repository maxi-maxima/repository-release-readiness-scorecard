# repository-release-readiness-scorecard

Score whether an open-source repository is ready for a trustworthy public launch.

## Pain Point

AI agents, MCP servers, cost controls, release gates, and creator workflows are moving fast, but many teams still lack tiny local tools that can be dropped into CI or run from a terminal without shipping private data to another SaaS product.

## Why Now

June 2026 trend research showed strong momentum around MCP as the agent integration standard, CLI-first coding agents, verification bottlenecks, agent security controls, practical cost governance, and content automation. This project targets one of those high-signal operational gaps with a small auditable utility.

## Install

```bash
python -m venv .venv
. .venv/Scripts/activate  # Windows Git Bash
pip install -e .
```

No runtime dependencies are required beyond Python's standard library.

## Run

```bash
python -m repository_release_readiness_scorecard examples/sample-repo
python -m repository_release_readiness_scorecard . --min-score 70
python -m repository_release_readiness_scorecard . --min-score 70 --require-check LICENSE --require-check tests
python -m repository_release_readiness_scorecard . --markdown
python -m repository_release_readiness_scorecard . --markdown --output readiness-report.md
```

`--min-score` lets CI choose its own release gate. The default remains `80`, while lower values are useful for advisory reports during early project setup. `--require-check` can additionally make specific release hygiene checks mandatory even when the aggregate score is acceptable.

Use `--markdown` when you want a PR-ready table for issue comments, release
reviews, or CI summary uploads. Add `--output <path>` to persist the exact same
rendered report as a CI artifact while still printing it to stdout.

## Example Output

Run the command above against files in `examples/` to see deterministic output suitable for demos, issue reports, and CI logs.

## Self Check

```bash
python -m unittest discover -s tests
```

## Roadmap

- Add richer machine-readable output for CI annotations.
- Add more real-world fixtures from popular agent and MCP workflows.
- Publish packaged binaries for users without Python environments.
- Add GitHub Action examples for pull-request automation.

## License

MIT
