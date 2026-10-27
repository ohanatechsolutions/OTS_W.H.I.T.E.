# Changelog

## Unreleased — OTS W.H.I.T.E. (White Hat Infiltration Testing Engine) rebrand

- Rebranded user-facing software, package/CLI identifiers, documentation, Windows installer, and release artifacts to OTS W.H.I.T.E. / OTS_WHITE.
- Renamed importable package to `ots_white`, and updated launch scripts, tests, and workflow paths accordingly.
- Preserved existing repository security-audit behavior; no new remote GitHub authentication or scanning added by this rename.
- Main-branch Windows packaging now refreshes the rebranded executable installer and SHA-256 manifest in `installer/`.


This project records shipped changes by version and pending repository work under **Unreleased**; no new application version is implied by the latter.

## [Unreleased]

### Repository maintenance
- Added project-specific privacy, contribution, third-party notice and engineering/deployment/troubleshooting documentation.
- Established .editorconfig, broader Git ignore rules, CODEOWNERS, Dependabot and GitHub contribution templates.
- Prior Windows packaging used Actions artifacts without committing additional installers; the rebrand enables publishing current installer binaries and SHA-256 manifests into `installer/`. Version tags are configured to publish installer and matching checksum as GitHub Release assets; successful builds continue to upload temporary Actions artifacts.
- Updated private vulnerability reporting and maintainer guidance. No application scanning or GUI behavior was intentionally changed.


## v0.1.0 — initial public-code baseline (2026-10-24, Hawaii)

- Offline built-in credential detection, high-entropy heuristics, and basic SAST/configuration checks.
- Locally reachable Git history scanning and changed-path PR comparison using Git plumbing.
- OSV-Scanner v2 offline SCA adapter (external scanner/database needed; no remote private-code submission).
- Redacted terminal/JSON/SARIF output and fail-closed operational exit code.
- Local Python/Tk Windows GUI, Windows launchers, installable Python package.
- GitHub Actions security/tests workflow with least-privilege contents read.
- Windows executable and unsigned Inno Setup installer build, with SHA-256 checksum artifact.
- 19 regression tests passing on Ubuntu and Windows CI runners.

### Release qualification

Build and checksum are verified; no claim of code signing, production-grade taint analysis, full coverage of GitHub remote PRs, live offline OSV database integration, or interactive Windows machine acceptance testing is made. See `docs/TEST_PLAN.md`, `SECURITY.md`, and `installer/README.md`.
