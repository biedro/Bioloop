# Contributing

Contributions are welcome.

## Development

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m pytest
```

## Privacy Expectations

Do not add telemetry, analytics, remote logging, or third-party data sharing without an explicit privacy review and documentation update.

Do not include real Oura data in tests, screenshots, examples, pull requests, or issues. Use synthetic fixtures only.
