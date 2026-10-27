"""Local Git object/history support; never executes repository code or hooks."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess


class GitScanError(RuntimeError):
    pass


def git(root: Path, *args: str, input_data: bytes | None = None, timeout: int = 90) -> bytes:
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1", "GIT_TERMINAL_PROMPT": "0"}
    try:
        p = subprocess.run(["git", "-C", str(root), *args], input=input_data,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                           check=False, env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise GitScanError(f"Git command failed or timed out: {args[0]}") from e
    if p.returncode:
        # Deliberately do not echo Git stderr: paths/remotes may be private.
        raise GitScanError(f"Git returned exit code {p.returncode} for {args[0]}")
    return p.stdout


def is_git_repo(root: Path) -> bool:
    try:
        return git(root, "rev-parse", "--is-inside-work-tree").strip() == b"true"
    except GitScanError:
        return False


def changed_paths(root: Path, base: str) -> set[str]:
    # Reject user-supplied options and expressions; Git ref input is always a single arg.
    if not base or base.startswith("-") or "\x00" in base or ".." in base or len(base) > 200:
        raise GitScanError("Invalid base ref; supply a local branch name or SHA")
    output = git(root, "diff", "--name-only", "--diff-filter=ACMR", "-z", f"{base}...HEAD", "--")
    return {os.fsdecode(p).replace("\\", "/") for p in output.split(b"\x00") if p}


def historical_blobs(root: Path, max_bytes: int, max_blobs: int = 100_000):
    """Yield (blob SHA, historical path, UTF-8 text). Includes deleted/replaced blobs.

    Git object traversal is repository-wide, including all local refs; fetch all history
    before invoking this for remote repos. A cap protects from unbounded work.
    """
    objects = git(root, "rev-list", "--objects", "--all", timeout=180).splitlines()
    if len(objects) > max_blobs * 4:
        raise GitScanError("History has too many Git objects; narrow the repository or raise limits")
    shas: list[bytes] = []
    paths: dict[str, str] = {}
    for obj in objects:
        sha, _, path = obj.partition(b" ")
        if len(sha) not in (40, 64) or not all(c in b"0123456789abcdef" for c in sha):
            continue
        key = sha.decode("ascii")
        shas.append(sha)
        paths[key] = os.fsdecode(path) if path else "[historical object]"
    if not shas:
        return
    # One batch stat call avoids spawning a process per object.
    data = git(root, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
               input_data=b"\n".join(shas) + b"\n", timeout=180)
    count = 0
    for row in data.splitlines():
        try:
            sha, kind, size = row.decode("ascii").split(" ")
            nbytes = int(size)
        except (UnicodeError, ValueError):
            continue
        if kind != "blob" or nbytes > max_bytes:
            continue
        count += 1
        if count > max_blobs:
            raise GitScanError("History exceeded configured blob cap")
        blob = git(root, "cat-file", "blob", sha, timeout=20)
        if b"\x00" in blob[:8192]:
            continue
        text = blob.decode("utf-8", errors="replace")
        yield sha, paths.get(sha, "[historical object]"), text


def introducing_commit(root: Path, blob_sha: str) -> str:
    # Best-effort first reachable commit touching the object; not always first exposure.
    try:
        commits = git(root, "log", "--all", "--format=%H", "-1", f"--find-object={blob_sha}", timeout=15)
        return commits.decode("ascii").strip()[:64] or "unknown"
    except (GitScanError, UnicodeError):
        return "unknown"
