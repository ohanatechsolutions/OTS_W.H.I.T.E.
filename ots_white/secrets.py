"""Bounded, local secret heuristics. Findings deliberately contain no matched values."""
from __future__ import annotations
import math
import re
from collections import Counter
from .model import Finding

# These signatures are indicative, not verification that a credential is active.
SIGNATURES = (
    ("SECRET-AWS", "high", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"), "AWS access key identifier"),
    ("SECRET-GITHUB", "critical", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b"), "GitHub token"),
    ("SECRET-SLACK", "high", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b"), "Slack token"),
    ("SECRET-STRIPE", "critical", re.compile(r"\b(?:sk_live|rk_live)_[A-Za-z0-9]{16,}\b"), "Stripe live secret key"),
    ("SECRET-GOOGLE", "high", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"), "Google API key"),
    ("SECRET-PEM", "critical", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"), "Private key material"),
    ("SECRET-CONNECTION", "high", re.compile(r"\b(?:postgres(?:ql)?|mongodb(?:\+srv)?|mysql|redis)://[^\s'\"]+:[^@\s'\"]+@", re.I), "Embedded database connection credential"),
)
ASSIGNMENT = re.compile(
    r"(?i)\b(?:password|passwd|pwd|secret(?:_key)?|api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)"
    r"\b\s*[=:]\s*['\"]?([^\s'\";,\}]{8,})"
)
ENTROPY_CANDIDATE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{40,200}(?![A-Za-z0-9+/=_-])")
ENTROPY_CONTEXT = re.compile(r"(?i)\b(?:token|credential|secret|password|api[_-]?key|auth|bearer)\b")
LOCKFILE_NAMES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "composer.lock", "Cargo.lock", "poetry.lock", "Gemfile.lock"}
PLACEHOLDERS = re.compile(r"(?i)^(?:\$\{|\$\(|\$|%|\{\{|\<|your[_-]|example|placeholder|changeme|replace|dummy|fake|test|xxxx|\*{2}|null|undefined|none|true|false)")


def entropy(value: str) -> float:
    if not value:
        return 0
    counts = Counter(value)
    return -sum((n / len(value)) * math.log2(n / len(value)) for n in counts.values())


def scan_secrets(text: str, path: str) -> list[Finding]:
    found: list[Finding] = []
    for number, line in enumerate(text.splitlines(), 1):
        if len(line) > 20_000:
            # Treat minified or massive single lines as candidates for signature scanning,
            # but cap work and report an explicit partial-coverage condition in pipeline.
            continue
        if "ots-white: allow-secret" in line or "aegis-white: allow-secret" in line:
            # Only inline, deliberate opt-out, reviewed like any other code change.
            continue
        for rule, severity, pattern, name in SIGNATURES:
            for match in pattern.finditer(line):
                found.append(Finding(rule, "secret", severity, f"Possible {name} (value redacted)", path,
                                     number, match.start()+1, "Revoke/rotate if real; remove from all history and use a secret manager."))
        assignment_spans = []
        for match in ASSIGNMENT.finditer(line):
            candidate = match.group(1)
            assignment_spans.append(match.span(1))
            if PLACEHOLDERS.match(candidate) or candidate.lower().startswith(("http://", "https://", "process.env.", "os.environ", "getenv(", "env[", "settings.", "config.")):
                continue
            if len(candidate) >= 12 and entropy(candidate) >= 3.2 or (len(candidate) >= 8 and re.search(r"(?i)password|passwd|pwd", match.group(0)) and entropy(candidate) >= 2.6):
                found.append(Finding("SECRET-ASSIGNMENT", "secret", "high",
                                     "Possible hardcoded credential assignment (value redacted)", path,
                                     number, match.start()+1, "Replace literal with a runtime secret source and rotate any exposed credential."))
        # Conservative entropy-only heuristic: require security context or a .env file.
        # Avoid normal dependency lock integrity hashes and already reported assignments.
        if path.rsplit("/", 1)[-1] not in LOCKFILE_NAMES and (ENTROPY_CONTEXT.search(line) or ".env" in path.rsplit("/", 1)[-1]):
            for match in ENTROPY_CANDIDATE.finditer(line):
                token = match.group()
                if any(a <= match.start() and match.end() <= b for a, b in assignment_spans):
                    continue
                if (not PLACEHOLDERS.match(token) and len(set(token)) >= 12
                        and re.search(r"[A-Za-z]", token) and re.search(r"[0-9]", token)
                        and entropy(token) >= 4.6):
                    found.append(Finding("SECRET-HIGH-ENTROPY", "secret", "medium",
                                         "High-entropy credential-like string (value redacted)", path,
                                         number, match.start()+1, "Investigate whether this is a real credential; rotate and relocate if confirmed."))
    return found
