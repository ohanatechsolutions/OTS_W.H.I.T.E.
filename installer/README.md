# Windows installer

**The Windows installer is an `.exe`, not the `.iss` source recipe.** The Inno Setup file in this folder is used by the automated build; it is not itself a runnable installer.

## Ready-to-download v0.1.0

[Download the Windows installer artifact from the successful GitHub Actions build](https://github.com/ohanatechsolutions/Aegis_White/actions/runs/40173916046).

Expand **Artifacts** and download `AegisWhite-Windows-Installer`. Unzip it to get:

- `AegisWhite_Setup_v0.1.0_x64.exe` — the Windows 10/11 x64 installer.
- `AegisWhite_Setup_v0.1.0_x64.exe.sha256` — the checksum manifest.

Installer SHA-256 from this specific run:

`752aea471a6da38bcb4c19fd1f1c6b54eb24225e08289273df75c29a06d60d9a`

To verify in PowerShell:

```powershell
(Get-FileHash .\AegisWhite_Setup_v0.1.0_x64.exe -Algorithm SHA256).Hash.ToLowerInvariant()
```

Compare its result with the above digest before installing. This release is **unsigned**; do not mistake a Windows SmartScreen warning for proof of tampering, or the absence of a warning for proof of security.

## Building another installer

Use **Actions → Windows Installer → Run workflow**. The workflow runs unit tests, packages the Tk GUI with PyInstaller, compiles the Inno Setup recipe, creates a fresh SHA-256 file, and uploads both as a GitHub Actions artifact. No paid installer tooling or runtime subscription is required.

The installer packages the GUI; OSV-Scanner v2 and its offline advisory cache are independently installed when SCA is desired. Live offline OSV integration and manual Windows GUI runtime/installation checks are still release acceptance items.
