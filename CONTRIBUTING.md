# Contributing

Contributions are welcome.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
```

## Product and UX Constitution

Before making product-facing changes, read [docs/PRODUCT_UX_CONSTITUTION.md](docs/PRODUCT_UX_CONSTITUTION.md), [docs/PRODUCT_EXPERIENCE_DESIGN.md](docs/PRODUCT_EXPERIENCE_DESIGN.md), and [docs/VISUAL_REFERENCES.md](docs/VISUAL_REFERENCES.md).

Bioloop is artifact-first, not dashboard-first. Prioritize Stories, Artifacts, Timeline, Studio, and Settings / Privacy. The first experience should create emotional recognition through a beautiful artifact, especially Life Rings, before exposing metrics, controls, or analysis.

Avoid metric-dashboard homepages, chatbot-first navigation, red/green scoring systems, gamification, streaks, leaderboards, medical claims, and raw health values in shared outputs by default.

## Privacy Expectations

Do not add telemetry, analytics, remote logging, or third-party data sharing without an explicit privacy review and documentation update.

Do not include real Oura data in tests, screenshots, examples, pull requests, or issues. Use synthetic fixtures only.
