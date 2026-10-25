# Troubleshooting

## `.iss` opens “choose an app”

An `.iss` file is the **Inno Setup script**, not an executable installer. Download the `.exe` and `.sha256` from a successful [Windows Installer workflow](../installer/README.md), or from a versioned GitHub Release when one has been published.

## GUI will not start

Use Python 3.11+ with Tkinter available. From the repository folder:

```powershell
py -3 -m aegis_white.gui
```

For command-line scanning without Tkinter, use `py -3 -m aegis_white . --no-sca`. A packaged Windows installer contains a GUI executable, but it does not install Python or the optional OSV-Scanner.

## Exit code 2 or “audit incomplete”

The scanner intentionally fails rather than claiming a clean scan if a requested module cannot complete. Look for missing OSV-Scanner, uninitialized/stale offline advisory database, missing Git base ref, unreadable/oversized files, or unavailable history. Run `--no-sca` only if intentionally skipping dependency scanning, and report that limitation.

## SCA reports no data or fails

Install a trusted OSV-Scanner **v2**, populate its offline advisory database **outside the private repository**, and check the current OSV CLI documentation for database initialization. The scan itself uses `--offline --no-resolve`, so it will not fetch packages or advisories. Offline mode does not guarantee coverage for every ecosystem or an unpinned requirements file.

## Git history / PR inspection appears incomplete

A source ZIP has no Git object history; obtain a full clone and fetch relevant refs. `--base` works only with a locally available base branch and scans changed working-tree paths, not every remotely open pull request. `--history` scans locally reachable blobs, not inaccessible remote objects.

## Unexpected secret/SAST warning

Review the rule, file and location privately. Never post the suspected value in a public issue. See [README.md](../README.md) for narrow `--exclude` patterns and reviewed inline suppressions. Rotate real leaked credentials **before** attempting history cleanup.

## Windows warns about the installer

The current build is unsigned, so Windows SmartScreen can display a warning. Verify the SHA-256 against the matching trusted artifact and review its source. A checksum does not authenticate the publisher; obtain signed software when a signed release becomes available.

For reproducible test steps, see [DEVELOPMENT.md](DEVELOPMENT.md). Report security vulnerabilities privately following [SECURITY.md](../SECURITY.md).
