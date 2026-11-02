#!/usr/bin/env python3
"""Read-only prepublication audit of eight private GitHub repositories.

Prerequisites: Python >=3.11, git, gh (authenticated), and Gitleaks >=8.19.
No raw detected values are placed in the report. The script never changes repos.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPOS = (
    'ohanatechsolutions/OTS_System_Santizer',
    'ohanatechsolutions/OTS_W.H.I.T.E.',
    'ohanatechsolutions/AI-Development-Prompts',
    'ohanatechsolutions/OTS_Clipboard_History',
    'ohanatechsolutions/OTS_Firewall79X',
    'ICF-AI/ICF_AI_HQ',
    'ICF-AI/AI_Efficiency_Toolkit',
    'ICF-AI/ICF_Chrome_Extension',
)

# Detection-only: never preserve matched values in generated reports.
SECRET = re.compile(
    rb'gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,}'
    rb'|\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|AIza[A-Za-z0-9_-]{35}'
    rb'|(?:sk_live|rk_live)_[A-Za-z0-9]{16,}'
    rb'|xox[baprs]-[A-Za-z0-9-]{12,}'
    rb'|-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----'
    rb'|(?:postgres(?:ql)?|mongodb(?:\+srv)?|mysql|redis)://[^\s:@/]+:[^\s@/]+@',
    re.IGNORECASE,
)
ARCHIVE_MAX_BYTES = 512 * 1024 * 1024
TEXT_SCAN_CHUNK = 2 * 1024 * 1024


def command(argv: list[str], *, cwd: Path | None = None, timeout: int = 3600,
            env: dict[str, str] | None = None, permit_failure: bool = False) -> subprocess.CompletedProcess[str]:
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                       errors='replace', timeout=timeout, check=False)
    if p.returncode and not permit_failure:
        # Do not echo stderr: Git/gh may emit private URL or token data.
        raise RuntimeError(f'{argv[0]} returned exit code {p.returncode}')
    return p


def scan_stream(stream, *, max_bytes: int = ARCHIVE_MAX_BYTES) -> tuple[bool, int]:
    found = False
    consumed = 0
    previous = b''
    while True:
        chunk = stream.read(TEXT_SCAN_CHUNK)
        if not chunk:
            break
        consumed += len(chunk)
        if consumed > max_bytes:
            raise ValueError('file exceeded bounded inspection limit')
        joined = previous + chunk
        # UTF-16LE is common in Windows binaries and configuration resources.
        if SECRET.search(joined) or SECRET.search(joined[::2]) or SECRET.search(joined[1::2]):
            found = True
        previous = joined[-512:]
    return found, consumed


def scan_path(path: Path, *, depth: int = 0) -> dict:
    result = {'name': path.name, 'possible_credentials': False, 'incomplete': False,
              'archive_entries': 0, 'reason': ''}
    try:
        with path.open('rb') as f:
            result['possible_credentials'], _ = scan_stream(f)
        if path.suffix.lower() in {'.zip', '.jar', '.nupkg'} and depth < 2:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                result['archive_entries'] = len(entries)
                for item in entries:
                    if item.is_dir():
                        continue
                    if item.file_size > ARCHIVE_MAX_BYTES:
                        result['incomplete'] = True
                        result['reason'] = 'oversized archive member'
                        continue
                    with archive.open(item, 'r') as entry:
                        try:
                            matched, _ = scan_stream(entry)
                            result['possible_credentials'] |= matched
                        except ValueError:
                            result['incomplete'] = True
                            result['reason'] = 'archive expansion limit'
                # Nested archives require a separate bounded inspection.
                if any(x.filename.lower().endswith(('.zip', '.7z', '.rar', '.tar.gz')) for x in entries):
                    result['incomplete'] = True
                    result['reason'] = 'nested archive requires manual inspection'
        elif path.suffix.lower() in {'.7z', '.rar', '.tar', '.gz'}:
            result['incomplete'] = True
            result['reason'] = 'unsupported archive format'
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as exc:
        result['incomplete'] = True
        result['reason'] = type(exc).__name__
    return result


def gitleaks(repo: Path, destination: Path) -> dict:
    raw = destination / 'gitleaks-private.json'
    try:
        p = command(['gitleaks', 'git', '--no-banner', '--redact=100',
                     '--log-opts=--all', '--report-format=json', '--report-path', str(raw),
                     str(repo)], cwd=repo, timeout=3600, permit_failure=True)
        if p.returncode not in (0, 1):
            return {'complete': False, 'finding_count': None, 'error': 'scanner process failed'}
        try:
            data = json.loads(raw.read_text(encoding='utf-8')) if raw.exists() else []
            if not isinstance(data, list):
                raise ValueError('report must be a list')
            return {'complete': True, 'finding_count': len(data),
                    'rules': sorted({str(x.get('RuleID', 'unknown')) for x in data})}
        except (ValueError, OSError):
            return {'complete': False, 'finding_count': None, 'error': 'unreadable scan report'}
    finally:
        # The raw report may contain surrounding context despite redaction.
        raw.unlink(missing_ok=True)


def auth_environment() -> dict[str, str]:
    env = dict(os.environ)
    env.update({'GIT_TERMINAL_PROMPT': '0', 'GH_PROMPT_DISABLED': '1',
                'GIT_LFS_SKIP_SMUDGE': '1', 'GIT_NO_REPLACE_OBJECTS': '1'})
    return env


def audit_repo(full_name: str, root: Path) -> dict:
    name = full_name.split('/')[-1].rstrip('.')
    dest = root / (full_name.split('/')[0] + '_' + name)
    env = auth_environment()
    report = {'repository': full_name, 'complete': False, 'history': {},
              'releases': {}, 'unverified_binaries': [], 'warnings': []}
    try:
        command(['gh', 'repo', 'clone', full_name, str(dest), '--', '--no-checkout'],
                env=env, timeout=1800)
        command(['git', 'fetch', '--all', '--tags', '--prune'], cwd=dest, env=env, timeout=1800)
        # Pull-request heads can contain unmerged or subsequently deleted material.
        pr_list = command(['git', 'ls-remote', 'origin', 'refs/pull/*/head'],
                          cwd=dest, env=env, timeout=1800)
        if pr_list.stdout.strip():
            command(['git', 'fetch', 'origin', '+refs/pull/*/head:refs/audit/pr/*'],
                    cwd=dest, env=env, timeout=1800)
        refs = command(['git', 'for-each-ref', '--format=%(refname)'], cwd=dest, env=env)
        report['history']['refs'] = len(refs.stdout.splitlines())
        count = command(['git', 'rev-list', '--count', '--all'], cwd=dest, env=env)
        report['history']['commits'] = int(count.stdout.strip())
        report['history']['gitleaks'] = gitleaks(dest, root)
        try:
            from ots_white.cli import audit  # Independent built-in scanner on all historical blobs
            white_result = audit(dest, history=True, no_sca=True)
            report['history']['ots_white'] = {
                'complete': bool(white_result.complete),
                'scanned_history_blobs': white_result.scanned_history_blobs,
                'secret_findings': sum(f.category == 'secret' for f in white_result.findings),
            }
        except (ImportError, OSError, ValueError, RuntimeError):
            report['history']['ots_white'] = {'complete': False, 'reason': 'local scanner unavailable or failed'}
        ls = command(['git', 'rev-list', '--objects', '--all'], cwd=dest, env=env, timeout=1800)
        pointers = 0
        for row in ls.stdout.splitlines():
            # Git LFS payload bytes are not present in normal Git object history.
            if row.endswith(('.exe', '.zip', '.7z', '.dll', '.pfx', '.p12')):
                report['unverified_binaries'].append(row.split(' ', 1)[-1])
            if row.endswith(('.exe', '.zip', '.7z')):
                pointers += 1
        report['history']['binary_paths_requiring_review'] = len(set(report['unverified_binaries']))
        # All releases, not only the latest, are considered publication exposure.
        release_json = command(['gh', 'api', '--paginate', '--slurp',
                                f'repos/{full_name}/releases?per_page=100'], env=env,
                               timeout=1800).stdout.strip()
        pages = json.loads(release_json) if release_json else []
        if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
            raise RuntimeError('GitHub release listing incomplete')
        releases = [release for page in pages for release in page]
        report['releases'] = {'total': len(releases), 'assets': 0,
                              'possible_credentials': 0, 'incomplete_assets': 0}
        for n, release in enumerate(releases):
            if not release.get('assets'):
                continue
            tag = release['tag_name']
            folder = root / ('release-' + str(n))
            folder.mkdir(exist_ok=True)
            command(['gh', 'release', 'download', tag, '--repo', full_name,
                     '--dir', str(folder)], env=env, timeout=3600)
            for asset in release['assets']:
                report['releases']['assets'] += 1
                actual = folder / asset['name']
                if not actual.is_file():
                    report['releases']['incomplete_assets'] += 1
                    continue
                scan = scan_path(actual)
                report['releases']['possible_credentials'] += int(scan['possible_credentials'])
                report['releases']['incomplete_assets'] += int(scan['incomplete'])
            shutil.rmtree(folder)
        # This is a finding triage tool, NOT an automatic safety certification.
        report['complete'] = bool(report['history']['gitleaks']['complete'] and
                                  report['history']['ots_white']['complete'] and
                                  report['history']['gitleaks']['finding_count'] == 0 and
                                  report['history']['ots_white']['secret_findings'] == 0 and
                                  report['releases']['possible_credentials'] == 0 and
                                  report['releases']['incomplete_assets'] == 0 and
                                  not report['unverified_binaries'])
        if report['unverified_binaries']:
            report['warnings'].append('Historical executables/archives need independent AV and provenance review')
        if pointers:
            report['warnings'].append('Some historical binaries may be Git LFS pointers; LFS payloads were not downloaded or individually inspected')
        if report['history']['ots_white'].get('secret_findings'):
            report['warnings'].append('OTS W.H.I.T.E. secret findings require human triage')
        if report['history']['gitleaks']['finding_count']:
            report['warnings'].append('Secret-scanner findings require human confirmation and rotation where applicable')
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        report['warnings'].append(f'Audit incomplete: {type(exc).__name__}')
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description='Redacted read-only public-release security inventory')
    parser.add_argument('--repo', action='append', choices=REPOS,
                        help='Restrict to specified repository (repeatable); default all eight')
    parser.add_argument('--output', default='publication-audit-results.json',
                        help='Private local JSON output file (never commit it)')
    args = parser.parse_args()
    if not all(shutil.which(tool) for tool in ('gh', 'git', 'gitleaks')):
        print('Required local tools: gh, git, and gitleaks.', file=sys.stderr)
        return 2
    check = command(['gh', 'auth', 'status'], env=auth_environment(), permit_failure=True)
    if check.returncode:
        print('GitHub CLI authentication is required for the private repositories.', file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix='ots-publication-audit-') as temp:
        results = [audit_repo(repo, Path(temp)) for repo in (args.repo or REPOS)]
    final = {'publication_cleared': False, 'repositories': results,
             'notice': 'This scan cannot set billing budgets or branch rules, verify full binary safety, or authorize public visibility. All scanner findings require independent review.'}
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(final, indent=2) + '\n', encoding='utf-8')
    if os.name == 'posix':
        out.chmod(0o600)
    print(f'Audit results saved (no secret values): {out}')
    for item in results:
        print(f"{item['repository']}: {'scanned' if item['complete'] else 'incomplete'}, "
              f"Gitleaks findings={item['history'].get('gitleaks', {}).get('finding_count')}, "
              f"release assets={item['releases'].get('assets', 0)}")
    return 0 if all(x['complete'] for x in results) else 2


if __name__ == '__main__':
    sys.exit(main())
