# Security policy and responsible disclosure

OTS W.H.I.T.E. is a defensive local repository auditor by Ohana Tech Solutions. Only scan code that you own or are authorized to inspect.

## Supported versions

| Version | Security maintenance |
|---|---|
| 0.1.x | Current baseline; security fixes evaluated on a case-by-case basis |
| Earlier / unreleased builds | Not supported |

There is no guaranteed support lifetime, response SLA, automatic updater or claim of independent security certification. Obtain updated builds through official repository Actions artifacts or versioned Releases when available.

## Report a vulnerability **privately**

Use GitHub's **Report a vulnerability** / private vulnerability reporting option on the repository's **Security** tab **if the owner has enabled it**. For this private repository, if that option is unavailable, contact the repository owner through an existing trusted private channel and ask for a secure reporting method. Do **not** use a public issue/PR or attach live keys, private repositories, full scan reports or working exploit payloads.

Provide the affected version, a concise explanation, minimal synthetic reproduction, impact, and a safe callback method. Maintainers will triage privately, assess severity and affected versions, prepare a fix as feasible, and coordinate disclosure after users have an opportunity to update. Timelines depend on severity and maintainer capacity; no fixed remediation deadline is promised. Coordinated disclosure is preferred over immediate publication.

## If a real secret is detected in a target repository

1. **Immediately revoke or rotate** the credential at its provider before relying on source cleanup.
2. Replace embedded values with a managed secret mechanism and least-privilege access.
3. Investigate the exposure window and affected service activity.
4. Coordinate any history rewrite with collaborators; old copies may persist in forks, caches, clones and logs.
5. Re-scan with full locally available history and independently verify credential revocation.

## Security properties and limitations

- The CLI/GUI read authorized local repositories; they do not intentionally upload source text, candidate secrets, or package inventories during scanning.
- Git history inspection uses Git plumbing and does not execute target code. An **externally installed, trusted** OSV-Scanner v2 is invoked using `--offline --no-resolve` for SCA.
- Standard console/GUI/JSON/SARIF findings are designed to omit raw matched credentials, source snippets and surrounding code. Paths, dependency metadata and commit IDs remain potentially sensitive.
- An unavailable scanner/database or materially unreadable inputs are operational errors (exit code 2), not a clean audit.
- Built-in SAST/secrets rules are heuristic and do not detect all vulnerabilities or secrets; missing/inaccessible Git refs and stale advisory caches limit coverage. Inline suppressions, exclusions and scan size caps can also produce misses.
- Third-party tooling, its installation, Python/Tcl/Tk runtimes, the operating system, and GitHub-hosted CI have separate trust boundaries. OTS W.H.I.T.E. does not revoke secrets or remediate detected vulnerabilities automatically.
- Users remain responsible for secure report storage and deletion; see [PRIVACY.md](PRIVACY.md).

Maintainers should review GitHub's available branch rulesets, private vulnerability reporting, Actions permissions and secret scanning settings for this private repository. Do not claim settings are enabled unless verified.
