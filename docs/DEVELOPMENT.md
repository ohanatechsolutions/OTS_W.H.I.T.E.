# Development guide

This guide supplements [README.md](../README.md) and [CONTRIBUTING.md](../CONTRIBUTING.md), without replacing either.

## Prerequisites and first checks

- Python 3.11 or newer (`python --version`; Windows: `py -3 --version`)
- Git for optional Git history / PR comparison scans
- Tkinter for the GUI (typically bundled with Windows Python; Linux may require a distribution package)
- Optional: trusted OSV-Scanner v2 and an **already populated local vulnerability database** for SCA
- Windows packaging only: Windows runner, PyInstaller 6.16.0 and Inno Setup 6

```powershell
python -m unittest discover -s tests -v
python -m ots_white --help
python -m ots_white . --no-sca --format table
python -m ots_white.gui
```

The last command requires a desktop session. Scanner exit codes are in [README.md](../README.md); exit code 2 signals incomplete or failed checks, not a clean audit.

## Main components

- `ots_white/cli.py` — CLI configuration, read-only file traversal and orchestrated checks
- `secrets.py` and `sast.py` — built-in local rule engine
- `git_scan.py` — locally reachable Git blobs and changed-path detection
- `sca.py` — invokes external OSV-Scanner v2 in `--offline --no-resolve` mode
- `model.py` and `reporting.py` — redacted finding schema, JSON/table/SARIF
- `gui.py` and `desktop_launcher.py` — Tk desktop application / packaged entry point
- `tests/test_ots_white.py` — standard-library test suite

Consult [ARCHITECTURE.md](ARCHITECTURE.md) for the trust boundary and [TEST_PLAN.md](TEST_PLAN.md) for unresolved acceptance coverage.

## Security expectations for changes

Treat input files, Git histories, and manifest paths as untrusted. Never execute target code. Do not put raw suspected secret values into exceptions, reports, logs or CI artifacts. Add regression tests for safe redaction, intentionally malformed inputs and incomplete-scan exit codes. SCA should never silently switch to an online call. Keep version numbers aligned across `pyproject.toml`, `installer/OTS_WHITE.iss`, and release notes.

GitHub CI runs tests and the **built-in checks without SCA**. This does not qualify full offline OSV database scanning. Avoid importing private scanning test data into public CI.
