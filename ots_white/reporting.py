"""Sanitized report output, including SARIF 2.1.0 for GitHub code scanning."""
from __future__ import annotations
import json
from .model import Finding, ScanReport, LEVELS


def as_sarif(report: ScanReport) -> dict:
    rules = {}
    for f in report.findings:
        rules[f.rule_id] = {
            "id": f.rule_id, "shortDescription": {"text": f.message},
            "help": {"text": f.recommendation or "Review this security finding."},
            "properties": {"security-severity": str({"critical": 9.5, "high": 8.0, "medium": 5.0, "low": 2.0, "info": 0.0}.get(f.severity, 5.0))},
        }
    results = []
    for f in report.findings:
        path = f.path if not f.path.startswith("git:") else f.path.split(":", 2)[-1]
        results.append({
            "ruleId": f.rule_id, "level": "error" if LEVELS[f.severity] >= 3 else "warning",
            "message": {"text": f.message},
            "locations": [{"physicalLocation": {"artifactLocation": {"uri": path},
                                               "region": {"startLine": f.line, "startColumn": f.column}}}],
            "partialFingerprints": {"otsWhite/location": f.fingerprint},
            "properties": {"category": f.category, "severity": f.severity, "reference": f.reference},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "OTS W.H.I.T.E.", "version": "0.1.0",
                                               "rules": list(rules.values())}},
                  "results": results,
                  "invocations": [{"executionSuccessful": report.complete,
                                   "toolExecutionNotifications": [{"level": "error", "message": {"text": e}} for e in report.errors]}]}],
    }


def render(report: ScanReport, fmt: str) -> str:
    if fmt == "json":
        return json.dumps(report.as_dict(), indent=2) + "\n"
    if fmt == "sarif":
        return json.dumps(as_sarif(report), indent=2) + "\n"
    lines = ["OTS W.H.I.T.E. — local repository security scan",
             f"Status: {'COMPLETE' if report.complete else 'INCOMPLETE'} | Files: {report.scanned_files} | History blobs: {report.scanned_history_blobs} | Findings: {len(report.findings)}"]
    for name, status in report.checks.items():
        lines.append(f"  {name}: {status}")
    for f in report.findings:
        lines.append(f"[{f.severity.upper():8}] {f.rule_id}  {f.path}:{f.line}  {f.message}")
    for issue in report.warnings:
        lines.append("WARNING: " + issue)
    for issue in report.errors:
        lines.append("ERROR: " + issue)
    return "\n".join(lines) + "\n"
