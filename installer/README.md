# Windows installer and checksums

An `.iss` file is **source configuration for Inno Setup**; it is not a runnable installer. Download the generated `.exe` and matching `.sha256` manifest.

## Existing v0.1.0 build

[Previously verified Windows installer artifact](https://github.com/ohanatechsolutions/Aegis_White/actions/runs/40173916046) — open **Artifacts**, download `AegisWhite-Windows-Installer`, and extract:

- `AegisWhite_Setup_v0.1.0_x64.exe` — unsigned Windows 10/11 x64 installer.
- `AegisWhite_Setup_v0.1.0_x64.exe.sha256` — matching checksum manifest.

The recorded checksum for **that specific earlier run** is:

`752aea471a6da38bcb4c19fd1f1c6b54eb24225e08289273df75c29a06d60d9a`

Artifacts expire according to GitHub retention settings (current workflow requests 30 days), so this link may no longer offer a download. New successful workflow runs produce fresh downloadable artifacts. **Version-tagged builds publish GitHub Release assets**; browse [Releases](https://github.com/ohanatechsolutions/Aegis_White/releases). This is a private repository, so GitHub access may be required.

## Produce your own installer

1. Open **Actions → Windows Installer → Run workflow** from the repository.
2. The Windows job runs unit tests, bundles the GUI with pinned PyInstaller, compiles `installer/AegisWhite.iss` with Inno Setup 6, creates a SHA-256 manifest, and uploads the pair.
3. Download both generated files from the successful run's **Artifacts** section. On a trusted Windows computer, verify the EXE against its own SHA-256 manifest:

```powershell
(Get-FileHash .\AegisWhite_Setup_v0.1.0_x64.exe -Algorithm SHA256).Hash.ToLowerInvariant()
Get-Content .\AegisWhite_Setup_v0.1.0_x64.exe.sha256
```

Compare the 64-character hex digest in both outputs. Checksums detect accidental or malicious modification **when the checksum source itself is trusted**; they are not a substitute for publisher code signing.

The workflow does **not** commit compiled installers back to Git; source and build recipes stay in the repository. Maintainers can publish a version-matched `v*` Git tag after review to trigger a GitHub Release. See [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md) for version checks and release steps.

## Release limitations

Installers are currently **unsigned**, so Windows SmartScreen may warn. An installer bundles the GUI, not OSV-Scanner v2 or its vulnerability database. Local Windows installation/uninstallation and genuine offline OSV SCA acceptance tests remain to be completed. Third-party bundled library licensing must be reviewed for each distributed build. See [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md).
