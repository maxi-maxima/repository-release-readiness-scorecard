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
```

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
