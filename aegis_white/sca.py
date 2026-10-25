"""OSV-Scanner v2 local/offline SCA adapter; no dependency data sent over network."""
from __future__ import annotations
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
from .model import Finding

_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,120}$")


class SCAScanError(RuntimeError):
    pass


def _severity(vuln: dict) -> str:
    sev = str(vuln.get("database_specific", {}).get("severity", "")).lower()
    if sev in ("critical", "high", "medium", "low"):
        return sev
    scores = vuln.get("severity") or []
    for score in scores:
        try:
            n = float(score.get("score", ""))
        except (ValueError, TypeError):
            continue
        return "critical" if n >= 9 else "high" if n >= 7 else "medium" if n >= 4 else "low"
    return "medium"  # Unrated advisory; not a verified severity.


def parse_osv_result(data: dict, root: Path) -> list[Finding]:
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        raise SCAScanError("Unexpected OSV JSON output (missing results array)")
    findings: list[Finding] = []
    for result in data["results"]:
        if not isinstance(result, dict):
            continue
        source = result.get("source") or {}
        raw_path = source.get("path", "")
        path = "[dependency manifest]"
        if isinstance(raw_path, str) and raw_path:
            absolute = Path(raw_path)
            try:
                path = str(absolute.resolve().relative_to(root.resolve())).replace("\\", "/")
            except ValueError:
                path = "[outside target repository]"
        for item in result.get("packages", []):
            if not isinstance(item, dict):
                continue
            pkg = item.get("package") or {}
            name = str(pkg.get("name", "unknown"))[:180]
            version = str(pkg.get("version", "unknown"))[:60]
            ecosystem = str(pkg.get("ecosystem", "unknown"))[:50]
            for advisory in item.get("vulnerabilities", []):
                if not isinstance(advisory, dict):
                    continue
                vid = str(advisory.get("id", ""))
                if not _ID.fullmatch(vid):
                    continue
                findings.append(Finding(f"SCA-{vid}", "sca", _severity(advisory),
                                        f"Known vulnerability {vid} in {ecosystem} {name}@{version}",
                                        path, 1, 1, "Review the advisory and upgrade to a patched version.",
                                        f"https://osv.dev/vulnerability/{vid}"))
    return findings


def scan_sca(root: Path, binary: str = "osv-scanner") -> list[Finding]:
    scanner = shutil.which(binary)
    if not scanner:
        raise SCAScanError("OSV-Scanner v2 not found in PATH. Install it and prepare its offline vulnerability database, or pass --no-sca.")
    # Important: --offline (not --offline-vulnerabilities) prevents all network.
    cmd = [scanner, "scan", "source", "--offline", "--no-resolve", "--recursive", "--format=json", str(root)]
    try:
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=300, env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, check=False)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise SCAScanError("Offline OSV scanner could not complete") from e
    if not process.stdout:
        raise SCAScanError("Offline OSV scan returned no JSON. Check local OSV database and CLI v2 installation.")
    try:
        report = json.loads(process.stdout)
    except (json.JSONDecodeError, UnicodeError) as e:
        raise SCAScanError("Offline OSV scan returned invalid JSON") from e
    # Non-zero exit 1 is often just vulnerabilities found; report must still be valid.
    if process.returncode not in (0, 1):
        raise SCAScanError(f"Offline OSV scan failed (exit {process.returncode}); check database and local logs")
    return parse_osv_result(report, root)
