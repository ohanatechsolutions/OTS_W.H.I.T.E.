# Privacy policy — Aegis White

**Applies to:** Aegis White 0.1.x, the local GUI and CLI maintained by Ohana Tech Solutions. Last reviewed: 2026-10-24.

## Data processed and purpose

Aegis White reads the local directory you select, and optionally locally available Git history, to identify potential leaked credentials, unsafe source/configuration patterns, and vulnerable dependencies. The built-in scanner processes source text and suspected secrets in memory, but its normal finding objects, console output, GUI, JSON and SARIF reports omit the raw secret values and code excerpts. Reports can contain **file paths, line/column positions, rule identifiers, advisory IDs, dependency names/versions and historical commit identifiers**. This metadata may still be confidential.

The GUI retains the latest report in application memory while open. The program does not create an account, request your name/email, track usage, install an analytics SDK or deliberately persist a history of scans. It does not automatically delete reports that *you* export.

## Storage and retention

- Source repositories and Git objects remain in their existing locations. Aegis White does not copy them to an application database.
- Reports are saved locally only when you choose an output path (CLI `--output` or GUI **Export report**). These files persist until you delete them; the application provides no automatic retention period or deletion service.
- The CLI attempts owner-only permissions (`0600`) for written reports on POSIX systems. The Windows GUI uses the destination directory's existing Windows permissions; check ACLs yourself.
- Do not put exported reports in public/shared folders or commit them to a repository. Delete them through your operating system when no longer needed.
- The core scanner has no application-managed cloud backup or telemetry archive.

## Network access and third parties

- Scanning a **local repository** with built-in secrets/SAST rules and Git tooling does not call a remote API.
- Dependency auditing invokes an **externally installed OSV-Scanner v2** using `--offline --no-resolve`; its vulnerability advisory cache must be prepared separately. Aegis White itself does not upload source, credentials, or dependency inventories to OSV or GitHub during a local scan.
- **Separate setup operations can use the network:** downloading Aegis White or OSV binaries, downloading/updating OSV's advisory database, and `git clone` / `git fetch` are initiated by the operator and handled by their respective tools.
- When you use **GitHub Actions** to test/build this project, the checked-out source, job logs, and build artifacts are processed and retained by GitHub according to GitHub's policies and repository settings. Do not confuse hosted CI with a fully offline local scan.
- There is no built-in GitHub OAuth login, SaaS service, automatic update checker, crash reporter, or analytics endpoint in version 0.1.x.

## Limits and incident handling

Redaction is designed to suppress matched credential values in standard findings; it cannot guarantee that arbitrary malicious file names, paths, dependency names, or unforeseen parser behavior will never expose sensitive text. Review reports before sharing. Do not send raw secrets in public bug reports. If credentials have been committed to a repository, rotate/revoke them immediately; scanning does not remediate historical exposure.

Security reports: follow [SECURITY.md](SECURITY.md). Changes to network or logging behavior require an updated privacy review before release.
