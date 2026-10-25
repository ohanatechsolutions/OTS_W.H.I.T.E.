# Third-party components and notices

Aegis White's **core Python package (0.1.0)** uses the Python standard library, including Tkinter for its GUI, and declares **no third-party runtime Python dependencies** in `pyproject.toml`. Python itself and its bundled Tcl/Tk libraries have their own copyright and license terms.

Tools used **outside** the core runtime:

| Component | Role | Distribution / licensing action |
|---|---|---|
| CPython + Tkinter / Tcl/Tk | Runs source GUI; runtime libraries may be bundled by PyInstaller | Retain licenses/notices for versions actually bundled in a Windows executable; consult python.org and Tcl/Tk distributions |
| setuptools | Python package build backend (`setuptools>=69`) | Development/build dependency; see https://github.com/pypa/setuptools/blob/main/LICENSE |
| PyInstaller 6.16.0 | Builds the Windows portable GUI executable | Build-time tool with bootloader/runtime licensing obligations; see https://github.com/pyinstaller/pyinstaller/blob/develop/COPYING.txt |
| Inno Setup 6 | Builds the Windows `.exe` installer | External installer compiler; review its distribution terms at https://jrsoftware.org/isinfo.php |
| OSV-Scanner v2 | **Optional**, separately supplied offline dependency auditor | Not bundled with Aegis White; https://github.com/google/osv-scanner/blob/main/LICENSE |
| Git | Optional locally installed tool for history and PR-diff scanning | Not bundled; https://git-scm.com/about/free-and-open-source |

GitHub Actions (`actions/checkout`, `actions/setup-python`, `actions/upload-artifact`, `actions/download-artifact`) are hosted build actions, **not dependencies shipped in the GUI installer**.

This document is an inventory, **not a substitute for the exact license notices for packaged binaries**. Before distributing a new compiled release, inspect the actual PyInstaller payload, bundled Python/Tcl/Tk distributions, and any transitive components; ship their applicable notices, and record any dependency/version changes. The original [MIT license](LICENSE) governs Aegis White's own source code and is preserved.

Last reviewed: 2026-10-24.
