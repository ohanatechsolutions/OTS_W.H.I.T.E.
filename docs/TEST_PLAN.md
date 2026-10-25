# Validation strategy

Automated tests with `python -m unittest discover -s tests -v` cover:

1. High-confidence secret signatures and private-key headers.
2. Contextual credential assignments, entropy, placeholders and line-level suppressions.
3. Private output (raw test tokens never appear in JSON, text, or SARIF).
4. Scoped Python/JavaScript/workflow SAST patterns.
5. OSV v2 JSON conversion and fail-closed behavior with missing binary.
6. Offline OSV flags asserted by mocks (`--offline` and `--no-resolve`).
7. Git history finds synthetic credentials removed from the worktree.
8. Local PR base comparison excludes unchanged files.
9. Symlink avoidance and explicit failure on too-large inputs.
10. CLI threshold exit codes and report structure.

**Not validated in this environment:** genuine OSV database matching (binary/cache absent); Windows .bat execution or GUI rendering (build runner is Linux); scanning a real private GitHub repository; upstream SARIF ingestion. These require local integration/acceptance testing.

Additional release gates before high-assurance use:
- Install a trusted OSV-Scanner v2 release, download its offline DB, and exercise a known vulnerable lockfile.
- Test installed GUI on Windows 10 and Windows 11, including wide/high-DPI layouts.
- Test a full `git clone --mirror` / normal full-clone history, unusual names, Git LFS pointers, sparse checkouts, giant monorepos, submodules.
- Add fuzz/property testing for adversarial content and case-insensitive paths.
- Benchmark bounded execution and memory for large histories.
- Broaden SAST with a taint-aware engine and vetted rules.
