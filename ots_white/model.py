"""Strict output models: no secret values or source excerpts are retained."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
import hashlib

LEVELS = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}


@dataclass(frozen=True)
class Finding:
    rule_id: str
    category: str
    severity: str
    message: str
    path: str
    line: int = 1
    column: int = 1
    recommendation: str = ""
    reference: str = ""

    @property
    def fingerprint(self) -> str:
        # Stable finding location identifier; never hashes the secret value.
        payload = f"{self.rule_id}\0{self.path}\0{self.line}\0{self.column}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]

    def as_dict(self) -> dict:
        return {**asdict(self), "fingerprint": self.fingerprint}


@dataclass
class ScanReport:
    findings: list[Finding] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    checks: dict[str, str] = field(default_factory=dict)
    scanned_files: int = 0
    scanned_history_blobs: int = 0

    @property
    def complete(self) -> bool:
        return not self.errors and all(v in ("completed", "skipped") for v in self.checks.values())

    def add(self, findings: list[Finding]) -> None:
        self.findings.extend(findings)

    def finish(self) -> None:
        self.findings = sorted(
            { (f.rule_id, f.path, f.line, f.column): f for f in self.findings }.values(),
            key=lambda f: (-LEVELS.get(f.severity, 0), f.path, f.line, f.rule_id),
        )

    def as_dict(self) -> dict:
        by_severity = {s: sum(f.severity == s for f in self.findings) for s in LEVELS}
        return {
            "tool": "OTS W.H.I.T.E.", "schema_version": "1.0", "complete": self.complete,
            "checks": self.checks, "scanned_files": self.scanned_files,
            "scanned_history_blobs": self.scanned_history_blobs,
            "summary": {"total": len(self.findings), "by_severity": by_severity},
            "findings": [f.as_dict() for f in self.findings],
            "warnings": self.warnings, "errors": self.errors,
        }
