# Contributing to OTS W.H.I.T.E.

Thanks for helping improve this defensive tool. Contributors must only test against repositories they own or are expressly authorized to inspect.

## Local development

1. Install Python 3.11+, Git, and (for the Tk GUI) your Python distribution's Tkinter support.
2. Clone this repository and work from a new branch.
3. The core scanner has no Python runtime dependencies. An optional editable install uses `python -m pip install -e .`, which may download build tools; inspect your environment first.
4. Run `python -m unittest discover -s tests -v`.
5. Smoke-test the CLI with `python -m ots_white . --no-sca --format table`. Exit code 1 means findings above the threshold, while 2 means incomplete coverage.
6. To exercise SCA, install a trusted OSV-Scanner v2 and prepare its offline advisory database **outside** any private target checkout. See [README.md](README.md).

## Contribution workflow

- Open an issue or discuss significant behavior changes first, then submit a small, descriptive pull request against `main`.
- Add or update regression tests for scanner rules, parsers, failure modes and redaction behavior. Keep fixtures fake; never commit working credentials or private data.
- Preserve the no-network-on-scan, fail-closed, and no-secret-in-findings security invariants.
- Keep changes compatible with Python 3.11+, Windows 10/11 and the documented CLI/API where practical.
- Follow [`.editorconfig`](.editorconfig): 4-space Python indentation, UTF-8/LF text, 2-space YAML/TOML formatting. Do not add new runtime dependencies without a threat/privacy and license review.
- PRs should state scope, commands actually run, expected limitations, and whether they affect privacy, packaging or release assets. Maintainers review prior to merging.

## Security issues

**Do not open public issues or pull requests containing live secrets or exploit details.** Use the private reporting instructions in [SECURITY.md](SECURITY.md). No guarantee of acceptance, merge or response time is implied.

Maintained by Ohana Tech Solutions. Contributions are licensed under the repository's existing [MIT license](LICENSE).
