# Security and responsible disclosure

Aegis White is a defensive local repository auditor. Use it only on repositories you own or are authorized to inspect. Do not publish unredacted secrets, private dependency manifests, or complete private scan reports in public issue trackers.

## If a real secret is detected

1. Immediately revoke or rotate the credential at its provider; rotation comes before deleting code.
2. Move credential storage to a managed secret source and use least-privilege access.
3. Investigate exposure windows and audit the affected service for misuse.
4. When appropriate, coordinate a history rewrite and purge with repository collaborators; note that forks, caches, clones, and logs can preserve the old key.
5. Re-run the full audit and verify the revocation succeeded at the provider.

## Reporting security flaws in Aegis White

Create a private security advisory through GitHub's security reporting facility once the repository has been published and configured, or contact the maintainer privately. Avoid including live credentials in a report. Do not submit secrets or exploitable private proof-of-concepts to public issues.

## Security goals

- No telemetry, no cloud-based secret validation, and no outgoing dependency queries at scan time.
- No execution of target repository code or dependency installation as part of a scan.
- No raw matched secrets in standard output, the GUI, or JSON/SARIF report models.
- Fail closed when required vulnerability database infrastructure is absent or the scan cannot cover material file inputs.

## Non-goals

This baseline does not prevent malicious code from operating if the scanned repository is separately built or executed. It cannot guarantee zero vulnerabilities, or recover credentials already harvested by attackers. OSV advisory cache freshness and the trustworthiness of external scanner binaries are operator responsibilities.
