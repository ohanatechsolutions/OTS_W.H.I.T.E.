# Aegis White

**Local-first, white-hat GitHub repository auditing** — by Ohana Tech Solutions.

Aegis White is a runnable, open-source Python desktop + CLI project that inspects **local GitHub repository checkouts** for accidental secrets, common unsafe code/configuration patterns, and known vulnerable dependencies. By default the dependency module invokes **OSV-Scanner v2 in fully offline mode**. It never sends private source files, secret candidates, or package inventories to a remote API.

> Only scan code you own or are authorized to audit. This tool is an auditing aid, not a guarantee that a repository is secure. It does not automatically rotate/revoke secrets, remediate bugs, or modify source code.

## What's included

| Module | Operation | Coverage |
|---|---|---|
| Secrets | Built in, offline | AWS/GitHub/Slack/Stripe/Google token shapes, PEM private key headers, embedded DB URLs, contextual hardcoded credential assignments and entropy checks |
| Git history | `--history`, offline | Traverses locally reachable historical Git blobs, including deleted/replaced files; indicates a corresponding commit when available |
| PR inspection | `--base main`, offline | Scans working-tree files whose paths changed in `main...HEAD` (fetch base ref first) |
| SAST | Built in, offline | Sample Python, JavaScript/TypeScript, Dockerfile, Terraform, GitHub Actions anti-patterns |
| SCA | OSV-Scanner v2 required | Compares recognized dependency manifests/lockfiles/SBOMs with an **already downloaded local OSV advisory cache** |
| Reporting | Built in | Redacted terminal, JSON, and SARIF 2.1.0; returns policy-friendly exit codes |
| Windows GUI | Built in | Choose a local repository, select scan modes, review findings, export sanitized reports |

**Privacy invariant:** Detection never places the matched credential, surrounding code, or source excerpts in findings/reports. Finding fingerprints are derived from rule and location only, not credential contents.

## Downloading the Windows installer

The repository includes a **Windows installer build workflow** at `.github/workflows/windows-installer.yml`. Run it from **Actions → Windows Installer → Run workflow** (or push a version tag). Once the run succeeds, download the `AegisWhite-Windows-Installer` artifact from that run. It contains a native `.exe` installer and its SHA-256 checksum file. The installer is **unsigned** until Ohana Tech Solutions provides a signing certificate; Windows SmartScreen may warn. The build uses GitHub-hosted Windows runners and therefore GitHub processes this project source; scanning of **target repositories** remains local to the end user.

Installers are **not** built directly in this source tree; do not mistake `installer/AegisWhite.iss` for a clickable installer. Verify the `.sha256` file against the downloaded `.exe` before launching it. The installed GUI requires neither Python nor pip. Offline OSV-Scanner is still a separate optional dependency.

## Windows 10 / 11: quick start

1. Install **Python 3.11 or newer** from https://www.python.org/downloads/ and enable **Add Python to PATH**. Windows Python installations generally include Tkinter (needed for the GUI).
2. Download and extract the `Aegis_White.zip` folder; do not execute inside an untrusted repository.
3. Double-click **`Launch_Aegis_White.bat`** in the extracted folder. It opens the local desktop interface; no installation or subscription is needed.
4. Select a locally downloaded/cloned GitHub repository, optionally enable **Scan Git history**, then click **Run Audit**.
5. For a working secrets + SAST audit **without OSV setup**, uncheck **Offline dependency SCA**. The result explicitly labels SCA as skipped.
6. To enable **full dependency auditing**, complete the OSV setup below first, then leave SCA checked.

If Python or the GUI fails to launch, open **PowerShell** in the extracted folder and run:

```powershell
py -3 -m aegis_white.gui
```

For a no-GUI audit, use the included `Run_Security_Scan.bat` (secrets/SAST/history only) or CLI:

```powershell
py -3 -m aegis_white "C:\Users\You\source\myrepo" --no-sca --history
```

## Get a GitHub repository onto your computer

Use a **full** clone (not a ZIP download) to inspect history:

```powershell
git clone https://github.com/OWNER/REPOSITORY.git
cd REPOSITORY
git fetch --all --tags
```

For a private repository, use Git Credential Manager or the GitHub CLI (`gh auth login`; `gh repo clone OWNER/REPOSITORY`). **Do not paste access tokens into URLs, command arguments, or chat.** The scanner itself accepts **local paths only** and does not authenticate to GitHub or use an API. A shallow clone, a GitHub-generated ZIP, and unfetched PR refs cannot provide complete history.

## Install OSV-Scanner v2 for SCA (one-time setup)

1. Download a **trusted official OSV-Scanner v2 release** for Windows/Linux/macOS at https://github.com/google/osv-scanner/releases (verify provenance and checksums as available). Place `osv-scanner.exe` on your Windows `PATH` or specify `--osv-binary C:\path\to\osv-scanner.exe`.
2. **Outside the private target repository**, download the public, offline OSV vulnerability cache while connected to the internet. The command below permits downloading advisory records; it does not scan/submit your repository:

```powershell
osv-scanner scan source --offline-vulnerabilities --download-offline-databases --format=json .
```

If your installed OSV v2 release expects a different syntax for database initialization, consult its own help and https://google.github.io/osv-scanner/usage/offline-mode/. Set `OSV_SCANNER_LOCAL_DB_CACHE_DIRECTORY` if storing the cache in a custom location. To verify the cache, disconnect from the internet and run the **actual private repository scan**:

```powershell
py -3 -m aegis_white "C:\Users\You\source\myrepo" --history --format table
```

Aegis White always runs OSV with `scan source --offline --no-resolve --recursive --format=json`. **It never updates the cache mid-scan**, and it fails with exit code 2 if OSV is missing or cannot return a valid result. Refresh advisory data periodically, separately from private scans. Confirm that your lockfiles/manifest formats are supported by your installed OSV-Scanner version.

**Important:** An offline scanner without its cache cannot determine whether dependencies are vulnerable. It must not be represented as a clean SCA audit.

## CLI examples

From the Aegis White folder, without installing any Python package:

```powershell
# Secrets + SAST, working tree only (no SCA)
py -3 -m aegis_white "C:\code\myrepo" --no-sca

# Secrets + SAST + all locally reachable commit history (no SCA)
py -3 -m aegis_white "C:\code\myrepo" --no-sca --history

# All modules, including fully offline OSV dependency auditing
py -3 -m aegis_white "C:\code\myrepo" --history

# Check the files changed in a PR after fetching base branch and checking out PR HEAD
py -3 -m aegis_white "C:\code\myrepo" --base main --no-sca

# Local JSON or SARIF report (secrets never serialized)
py -3 -m aegis_white "C:\code\myrepo" --no-sca --format json --output report.audit.json
py -3 -m aegis_white "C:\code\myrepo" --no-sca --format sarif --output report.sarif

# Custom size limit, exclusions, and severity threshold
py -3 -m aegis_white "C:\code\myrepo" --no-sca --max-file-bytes 10000000 --exclude "generated/**" --fail-on medium
```

If installing from source (optional):

```powershell
py -3 -m pip install .
aegis-white --help
aegis-white-gui
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Requested modules completed, no finding meets chosen `--fail-on` level |
| `1` | Requested modules completed and security findings meet threshold |
| `2` | Scan incomplete: missing offline scanner/cache, invalid Git ref, skipped oversize/unreadable inputs, or other operational error |

`--fail-on none` returns `0` even with findings **only if all requested modules completed**. Skipped SCA is explicitly labelled `skipped` when `--no-sca` is supplied.

## GitHub Actions integration

`.github/workflows/ci.yml` runs unit tests and a redacted secrets/SAST/history scan on push and pull request, with `contents: read` and no credentials persisted by checkout. It **does not** claim to perform dependency SCA, because a locally cached OSV database is not automatically available on a fresh GitHub-hosted runner. If you want CI SCA, provision a trusted database cache (or run a self-hosted offline runner) separately; never turn on online dependency resolution without reviewing disclosure implications.

If the scanner reports a secret in history, **rotate/revoke it first**, then coordinate any Git history rewrite with collaborators. Simply deleting the key in a later commit does not remove the old credential from history.

## Suppressions and scope

- Put `# aegis-white: allow-secret` or `# aegis-white: allow-sast` on a line only after explicit code-review approval for a known false positive. These markers affect the built-in matchers, not OSV advisories.
- Add `--exclude "path/glob"` to omit explicitly accepted paths. A directory named `.git`, `node_modules`, `vendor`, `.venv`, etc. is automatically excluded from **working-tree** inspection, but Git history still inspects reachable old blobs unless explicitly excluded.
- The scanner ignores symlinks, binary files, and other intentionally unsupported inputs. Oversized/unreadable text is reported as incomplete. Scan limits are adjustable.

## Documentation and project layout

```
Aegis_White/
  aegis_white/
    __main__.py, cli.py         CLI and traversal
    gui.py                      Optional Windows/Linux desktop UI
    secrets.py                  Credential signatures/entropy
    sast.py                     Lightweight SAST/config rules
    sca.py                      OSV v2 offline adapter
    git_scan.py                 Local Git history and PR comparison
    model.py, reporting.py      Structured redacted findings + SARIF
  tests/test_aegis_white.py    Local repeatable regression tests
  docs/ARCHITECTURE.md         Boundaries, threat model, limitations
  docs/TEST_PLAN.md            Coverage and unfinished acceptance gates
  .github/workflows/ci.yml     CI without privileged tokens
  Launch_Aegis_White.bat       Windows GUI launcher
  Run_Security_Scan.bat        Windows console launcher (no SCA)
  installer/AegisWhite.iss      Inno Setup recipe for native Windows .exe installer
  .github/workflows/windows-installer.yml Windows executable + installer + checksum
  pyproject.toml               Installable Python package
```

### Run tests

```powershell
py -3 -m unittest discover -s tests -v
```

## Future hardening priorities

This `0.1.0` release is a **tested baseline**, not a certified production-grade analyzer. Planned upgrades include taint-based SAST, additional secret provider validations via secure local verification, improved lockfile/SBOM diagnostics, signed release binaries for Windows, performance benchmarking on large monorepos, independent security review, and optional audited GitHub App integration with least-privilege read permissions. None of those enhancements is currently claimed as implemented.

License: MIT. Developer: **Ohana Tech Solutions** (Ohana Tech).
