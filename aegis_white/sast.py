"""Conservative SAST and misconfiguration rules, offline and read-only."""
from __future__ import annotations
import re
from .model import Finding

# Explicitly constrained to language/file families to reduce accidental matches.
RULES = (
    ("SAST-PY-EVAL", ".py", "high", r"\b(?:eval|exec)\s*\(", "Dynamic execution; verify inputs are trusted", "Use a restricted parser and avoid eval/exec on untrusted input."),
    ("SAST-PY-SHELL", ".py", "high", r"\bshell\s*=\s*True\b", "Subprocess shell enabled", "Use subprocess with an argument list and shell=False."),
    ("SAST-PY-PICKLE", ".py", "high", r"\bpickle\.(?:loads?|Unpickler)\s*\(", "Potential unsafe deserialization", "Never deserialize pickle from untrusted sources."),
    ("SAST-PY-YAML", ".py", "medium", r"\byaml\.load\s*\(", "Potential unsafe YAML parser", "Prefer yaml.safe_load for untrusted data."),
    ("SAST-PY-VERIFY", ".py", "high", r"\bverify\s*=\s*False\b", "TLS certificate verification disabled", "Keep TLS verification enabled."),
    ("SAST-PY-DEBUG", ".py", "medium", r"\bdebug\s*=\s*True\b", "Debug mode enabled (possibly production-exposed)", "Disable debug in production and restrict network access."),
    ("SAST-PY-PUBLIC", ".py", "medium", r"\bhost\s*=\s*['\"]0\.0\.0\.0['\"]", "Service bound on all IPv4 interfaces", "Verify authentication, firewall, and deployment network exposure."),
    ("SAST-JS-EVAL", (".js", ".jsx", ".ts", ".tsx"), "high", r"\b(?:eval|new\s+Function)\s*\(", "Dynamic JavaScript execution", "Avoid runtime code execution from data."),
    ("SAST-JS-CHILD", (".js", ".jsx", ".ts", ".tsx"), "medium", r"\b(?:child_process\.)?exec(?:Sync)?\s*\(", "Shell command execution surface", "Use execFile/spawn with separated arguments; validate input."),  # aegis-white: allow-sast (rule definition)
    ("SAST-JS-TLS", (".js", ".jsx", ".ts", ".tsx"), "high", r"rejectUnauthorized\s*:\s*false\b", "TLS certificate verification disabled", "Do not disable TLS identity checks."),
    ("SAST-JS-CORS", (".js", ".jsx", ".ts", ".tsx"), "medium", r"\borigin\s*:\s*['\"]\*['\"]", "Wildcard CORS origin configured", "Restrict origins when exposing authenticated or sensitive endpoints."),
    ("SAST-JS-PUBLIC", (".js", ".jsx", ".ts", ".tsx"), "low", r"\.listen\s*\([^\n]*['\"]0\.0\.0\.0['\"]", "HTTP listener binds on all interfaces", "Confirm endpoints have authentication and intended public network exposure."),
    ("CONFIG-WORKFLOW-PRIV", (".yml", ".yaml"), "high", r"\bpermissions\s*:\s*write-all\b", "Broad GitHub Actions token permissions", "Use granular permissions and read-only defaults."),
    ("CONFIG-DOCKER-ROOT", "Dockerfile", "medium", r"(?i)^\s*USER\s+(?:root|0)\s*$", "Container explicitly runs as root", "Use a non-root runtime user when possible."),
    ("CONFIG-TF-SG", ".tf", "high", r'cidr_blocks\s*=\s*\[\s*"0\.0\.0\.0/0"\s*\]', "Terraform security group permits all IPv4 addresses", "Verify exposure and restrict ingress to necessary CIDRs/ports."),
)
_COMPILED = [(code, suffix, level, re.compile(regex), title, fix) for code, suffix, level, regex, title, fix in RULES]


def scan_sast(text: str, path: str) -> list[Finding]:
    found: list[Finding] = []
    for i, line in enumerate(text.splitlines(), 1):
        if len(line) > 20_000 or "aegis-white: allow-sast" in line:
            continue
        stripped = line.lstrip()
        if stripped.startswith(("#", "//", "*")):
            continue
        for rule, suffix, level, pattern, title, fix in _COMPILED:
            if not (path.endswith(suffix) if isinstance(suffix, str) else path.endswith(suffix)):
                continue
            if rule == "CONFIG-WORKFLOW-PRIV" and not (".github/workflows/" in path.replace("\\", "/")):
                continue
            for match in pattern.finditer(line):
                found.append(Finding(rule, "sast", level, title, path, i, match.start()+1, fix))
    return found
