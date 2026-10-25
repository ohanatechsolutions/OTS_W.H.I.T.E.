# Aegis White — Windows installer

**The runnable Windows installer is checked into this folder as an `.exe`.**

- [Download the current Aegis White installer](https://github.com/ohanatechsolutions/Aegis_White/blob/main/installer/AegisWhite_Setup_v0.1.0_x64.exe)
- [Download the SHA-256 checksum manifest](https://github.com/ohanatechsolutions/Aegis_White/blob/main/installer/AegisWhite_Setup_v0.1.0_x64.exe.sha256)
- `AegisWhite.iss` is the **Inno Setup source recipe**, *not* the runnable installer.

Open the installer link while logged into the private GitHub account, then select **Download raw file** (or the download icon). The installer targets Windows 10/11 x64. It is unsigned.

## Verify the download

Run PowerShell in the folder where the .exe and .sha256 files were downloaded:

```powershell
(Get-FileHash .\AegisWhite_Setup_v0.1.0_x64.exe -Algorithm SHA256).Hash.ToLowerInvariant()
Get-Content .\AegisWhite_Setup_v0.1.0_x64.exe.sha256
```

Verify the digest matches the 64-character hexadecimal string in the matching `.sha256` file. Different builds may have different digests even with the same version number: **do not mix checksums from separate builds**.

## Build yourself / rebuild

Open [GitHub Actions → Windows Installer](https://github.com/ohanatechsolutions/Aegis_White/actions/workflows/windows-installer.yml) and select **Run workflow**. On source updates to `main`, the workflow runs the tests, builds the executable with PyInstaller, uses Inno Setup to create the Windows installer, generates a SHA-256 checksum, and commits both files into this folder. It also keeps the zipped installer in GitHub Actions artifacts for 30 days.

The installer packages the GUI. Offline SCA requires OSV-Scanner v2 and a populated offline database, which must be installed separately. Automated build and unit tests are not a substitute for manual installation/runtime acceptance testing.
