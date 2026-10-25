# Packaging and release procedure

Maintainer guide for the Python CLI and unsigned Windows 10/11 x64 GUI installer. See [installer instructions](../installer/README.md).

## Development checks

1. Review changes and run `python -m unittest discover -s tests -v`.
2. Run `python -m aegis_white . --no-sca --history --fail-on high` against a complete local checkout.
3. Update the **same version** in `pyproject.toml`, `installer/AegisWhite.iss`, the scanner's SARIF driver metadata in `aegis_white/reporting.py`, and `CHANGELOG.md`.
4. Review [PRIVACY.md](../PRIVACY.md), [SECURITY.md](../SECURITY.md), and [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md) whenever packaging, networking, or bundled dependencies change.
5. Check GitHub Actions status and review any security findings. Run Windows installer / GUI acceptance testing on a disposable Windows machine.

## Installer build

- `.github/workflows/windows-installer.yml` packages `desktop_launcher.py` with PyInstaller, compiles `installer/AegisWhite.iss` with Inno Setup 6, and produces an `.exe` with its `.sha256` file.
- Pushes to `main` and manual workflow dispatches upload the installer/checksum as **GitHub Actions artifacts** (subject to artifact retention); they do **not** commit generated installers to source control.
- Pushing a reviewed, annotated or lightweight version tag such as `v0.1.1` builds the installer and **publishes GitHub Release assets** after the build succeeds. The tag should match the installer version in source. Do not create a release from unreviewed source.
- On GitHub Actions, open **Windows Installer → latest successful run → Artifacts**. For tagged builds, find the assets under the repository's **Releases** tab.

Example tag publication after merging and validating a version bump:

```powershell
git fetch origin main --tags
git switch main
git pull --ff-only
git tag v0.1.1
git push origin v0.1.1
```

These commands are examples, **not** instructions to issue a tag for the current unbumped `0.1.0` source.

## Integrity and limitations

```powershell
(Get-FileHash .\AegisWhite_Setup_v0.1.0_x64.exe -Algorithm SHA256).Hash.ToLowerInvariant()
Get-Content .\AegisWhite_Setup_v0.1.0_x64.exe.sha256
```

Compare the computed digest with the checksum's hexadecimal string. A checksum detects mismatches **only if** its distribution source is trusted; it is not code signing. Installer binaries are currently unsigned and may trigger SmartScreen warnings. OSV-Scanner and its advisory cache are separate and not installed by the GUI installer. Release acceptance still requires actual Windows installation, GUI launch, uninstall checks, a bundled-library license review, and OSV offline integration against a known vulnerable package; see [TEST_PLAN.md](TEST_PLAN.md).

Do not attach unredacted private scan results or live secrets to releases, workflow logs or support tickets.
