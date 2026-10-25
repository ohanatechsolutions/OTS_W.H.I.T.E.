"""CLI entry point. All inspections read data, never execute the target project."""
from __future__ import annotations
import argparse
import fnmatch
import json
import os
from pathlib import Path
import sys
from .git_scan import GitScanError, changed_paths, historical_blobs, introducing_commit, is_git_repo
from .model import Finding, ScanReport, LEVELS
from .reporting import render
from .sast import scan_sast
from .sca import SCAScanError, scan_sca
from .secrets import scan_secrets

EXCLUDE_DIRS = {".git", ".hg", ".svn", "node_modules", "vendor", ".venv", "venv", "__pycache__", ".tox", "dist", "build", "coverage", ".next"}
MAX_DEPTH = 50


def enumerate_files(root: Path, excludes: list[str], base_paths: set[str] | None):
    for here, dirs, files in os.walk(root, topdown=True, followlinks=False):
        current = Path(here)
        relative_dir = current.relative_to(root)
        depth = len(relative_dir.parts)
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDE_DIRS and not (current / d).is_symlink()
                         and depth < MAX_DEPTH and not _excluded((relative_dir / d).as_posix(), excludes))
        for filename in sorted(files):
            full = current / filename
            rel = full.relative_to(root).as_posix()
            if full.is_symlink() or _excluded(rel, excludes):
                continue
            if base_paths is not None and rel not in base_paths:
                continue
            yield full, rel


def _excluded(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _read_text(file: Path, max_bytes: int) -> tuple[str | None, str | None]:
    try:
        if file.stat().st_size > max_bytes:
            return None, "oversize"
        with file.open("rb") as handle:
            raw = handle.read(max_bytes + 1)
        if len(raw) > max_bytes:
            return None, "oversize"
        if b"\x00" in raw[:8192]:
            return None, "binary"
        return raw.decode("utf-8", "replace"), None
    except (OSError, ValueError):
        return None, "unreadable"


def audit(root: Path, *, history: bool = False, base: str | None = None,
          no_sca: bool = False, max_file_bytes: int = 5_000_000,
          excludes: list[str] | None = None, osv_binary: str = "osv-scanner") -> ScanReport:
    result = ScanReport(checks={"secrets": "completed", "sast": "completed", "sca": "skipped" if no_sca else "pending"})
    excludes = excludes or []
    if not root.is_dir():
        result.errors.append("Target does not exist or is not a directory")
        return result
    if history and not is_git_repo(root):
        result.errors.append("--history requires a local Git working tree")
        result.checks["history"] = "failed"
    if base and not is_git_repo(root):
        result.errors.append("--base requires a local Git working tree")
        result.checks["pull_request_diff"] = "failed"
    changed = None
    if base and not result.errors:
        try:
            changed = changed_paths(root, base)
            result.checks["pull_request_diff"] = "completed"
        except GitScanError as e:
            result.errors.append(str(e))
            result.checks["pull_request_diff"] = "failed"
    skipped_large = 0
    skipped_unreadable = 0
    if not result.errors:
        for full, path in enumerate_files(root, excludes, changed):
            content, problem = _read_text(full, max_file_bytes)
            if content is None:
                skipped_large += problem == "oversize"
                skipped_unreadable += problem == "unreadable"
                continue
            result.scanned_files += 1
            result.add(scan_secrets(content, path))
            result.add(scan_sast(content, path))
            if any(len(line) > 20_000 for line in content.splitlines()):
                skipped_large += 1
        if skipped_large or skipped_unreadable:
            result.errors.append(f"File/line coverage incomplete: {skipped_large} size/line limits, {skipped_unreadable} unreadable files")
        if history and is_git_repo(root):
            result.checks["history"] = "pending"
            try:
                for sha, path, text in historical_blobs(root, max_file_bytes):
                    if _excluded(path, excludes):
                        continue
                    if any(len(line) > 20_000 for line in text.splitlines()):
                        result.errors.append("History coverage incomplete: oversized historical line")
                        continue
                    result.scanned_history_blobs += 1
                    history_findings = scan_secrets(text, f"git:{sha}:{path}")
                    if history_findings:
                        commit = introducing_commit(root, sha)
                        history_findings = [Finding(f.rule_id, f.category, f.severity,
                                            f"{f.message} [historical commit {commit}]", f.path,
                                            f.line, f.column, f.recommendation, f.reference) for f in history_findings]
                    result.add(history_findings)
                result.checks["history"] = "completed"
            except GitScanError as e:
                result.errors.append(str(e))
                result.checks["history"] = "failed"
    if not no_sca:
        try:
            result.add(scan_sca(root, binary=osv_binary))
            result.checks["sca"] = "completed"
        except SCAScanError as e:
            result.errors.append(str(e))
            result.checks["sca"] = "failed"
    result.finish()
    return result


def make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="aegis-white", description="Privacy-first local secrets, SAST, and offline SCA repository audit")
    p.add_argument("path", nargs="?", default=".", help="Local working tree (never a URL)")
    p.add_argument("--history", action="store_true", help="Inspect all locally available Git history, including deleted files")
    p.add_argument("--base", help="Scan changed working-tree files compared with base...HEAD (local PR scan)")
    p.add_argument("--no-sca", action="store_true", help="Explicitly skip offline vulnerability auditing")
    p.add_argument("--osv-binary", default="osv-scanner", help="Path or command of trusted OSV-Scanner v2")
    p.add_argument("--format", choices=("table", "json", "sarif"), default="table")
    p.add_argument("--output", help="Save report to a local file, no network")
    p.add_argument("--fail-on", choices=("info", "low", "medium", "high", "critical", "none"), default="high")
    p.add_argument("--max-file-bytes", type=int, default=5_000_000)
    p.add_argument("--exclude", action="append", default=[], metavar="GLOB", help="Exclude a path/pattern (repeatable)")
    return p


def main(argv: list[str] | None = None) -> int:
    p = make_parser()
    args = p.parse_args(argv)
    if args.max_file_bytes < 1024 or args.max_file_bytes > 100_000_000:
        p.error("--max-file-bytes must be between 1024 and 100000000")
    result = audit(Path(args.path).resolve(), history=args.history, base=args.base,
                   no_sca=args.no_sca, max_file_bytes=args.max_file_bytes,
                   excludes=args.exclude, osv_binary=args.osv_binary)
    output = render(result, args.format)
    if args.output:
        try:
            output_path = Path(args.output).expanduser().absolute()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            # Forbid symlinks and keep report private on POSIX; on Windows apply ACLs externally.
            if output_path.is_symlink():
                raise OSError("refusing to overwrite symlink")
            with output_path.open("w", encoding="utf-8") as target:
                target.write(output)
            if os.name == "posix":
                output_path.chmod(0o600)
            print(f"Aegis White report written: {output_path}", file=sys.stderr)
        except OSError:
            print("ERROR: could not write report", file=sys.stderr)
            return 2
    else:
        print(output, end="")
    if not result.complete:
        return 2  # Operational/configuration failure must not be mistaken for a clean scan.
    if args.fail_on != "none" and any(LEVELS[f.severity] >= LEVELS[args.fail_on] for f in result.findings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
