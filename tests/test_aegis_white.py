"""Regression tests. Fixtures use synthetic, nonfunctional credentials only."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from aegis_white.cli import audit, main
from aegis_white.git_scan import changed_paths
from aegis_white.model import ScanReport
from aegis_white.reporting import as_sarif, render
from aegis_white.sast import scan_sast
from aegis_white.sca import SCAScanError, parse_osv_result, scan_sca
from aegis_white.secrets import entropy, scan_secrets


class SecretTests(unittest.TestCase):
    def test_signature_and_redaction(self):
        synthetic = "ghp_" + "Ab3D" * 10
        found = scan_secrets("MY_TOKEN=" + synthetic, "config.env")
        self.assertTrue(any(f.rule_id == "SECRET-GITHUB" for f in found))
        report = ScanReport(found, checks={"secrets": "completed"})
        for output in (render(report, "json"), render(report, "table"), render(report, "sarif")):
            self.assertNotIn(synthetic, output)
        self.assertTrue(all(len(f.fingerprint) == 24 for f in found))

    def test_private_key_header(self):
        self.assertEqual(scan_secrets("-----BEGIN PRIVATE KEY-----", "x.key")[0].rule_id, "SECRET-PEM")  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)

    def test_placeholder_and_suppression(self):
        self.assertFalse(scan_secrets('password="your_password_here"', "x.py"))
        self.assertFalse(scan_secrets('password="SomeSecret1234!" # aegis-white: allow-secret', "x.py"))

    def test_assignment_entropy(self):
        self.assertGreater(entropy("AbC29Xfg$yT1"), 3.1)
        self.assertTrue(scan_secrets('password="AbC29Xfg$yT1"', "x.py"))  # aegis-white: allow-secret (synthetic test fixture)

    def test_high_entropy_token_in_context(self):
        import random
        rng = random.Random(42)
        alphabet = "ABCDEFGHIJKLMabcdefghijklm0123456789_-"
        simulated = "".join(rng.choice(alphabet) for _ in range(80))
        found = scan_secrets("credential: " + simulated, ".env.local")
        self.assertIn("SECRET-HIGH-ENTROPY", {f.rule_id for f in found})
        self.assertNotIn(simulated, repr(found))

    def test_non_secrets(self):
        self.assertFalse(scan_secrets('const api_key = process.env.API_KEY;', "app.js"))


class SASTTests(unittest.TestCase):
    def test_python(self):
        f = scan_sast("subprocess.run(cmd, shell=True)\nrequests.get(url, verify=False)", "app.py")  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)
        self.assertEqual({v.rule_id for v in f}, {"SAST-PY-SHELL", "SAST-PY-VERIFY"})

    def test_js(self):
        self.assertTrue(any(f.rule_id == "SAST-JS-TLS" for f in scan_sast("rejectUnauthorized: false", "main.ts")))

    def test_workflow_scoping(self):
        self.assertFalse(scan_sast("permissions: write-all", "config.yml"))
        self.assertTrue(scan_sast("permissions: write-all", ".github/workflows/test.yml"))


class AdapterTests(unittest.TestCase):
    def test_osv_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = {"results": [{"source": {"path": str(root / "go.mod")}, "packages": [
                {"package": {"name": "example.org/pkg", "version": "1.2.3", "ecosystem": "Go"},
                 "vulnerabilities": [{"id": "GHSA-aaaa-bbbb-cccc", "database_specific": {"severity": "HIGH"}}]}
            ]}]}
            out = parse_osv_result(data, root)
            self.assertEqual(out[0].rule_id, "SCA-GHSA-aaaa-bbbb-cccc")
            self.assertEqual(out[0].severity, "high")
            self.assertEqual(out[0].path, "go.mod")

    def test_osv_scanner_is_explicitly_offline(self):
        with tempfile.TemporaryDirectory() as td:
            fake_output = json.dumps({"results": []}).encode()
            with patch("aegis_white.sca.shutil.which", return_value="/mock/osv-scanner"), \
                 patch("aegis_white.sca.subprocess.run") as mock_run:
                mock_run.return_value.stdout = fake_output
                mock_run.return_value.returncode = 0
                self.assertEqual(scan_sca(Path(td)), [])
                cmd = mock_run.call_args.args[0]
                self.assertIn("--offline", cmd)
                self.assertIn("--no-resolve", cmd)
                self.assertEqual(cmd[1:3], ["scan", "source"])

    def test_missing_binary_fails_closed(self):
        with patch("aegis_white.sca.shutil.which", return_value=None):
            with self.assertRaises(SCAScanError):
                scan_sca(Path("."))

    def test_sarif_structure(self):
        report = ScanReport(scan_secrets("-----BEGIN RSA PRIVATE KEY-----", "key.pem"),  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)
                            checks={"secrets": "completed"})
        sarif = as_sarif(report)
        self.assertEqual(sarif["version"], "2.1.0")
        self.assertEqual(len(sarif["runs"][0]["results"]), 1)


class RepositoryTests(unittest.TestCase):
    def _git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def test_worktree_and_cli_exit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "bad.py").write_text('password="A7a9!Bk0PzG3"\nsubprocess.run(command, shell=True)\n')  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)
            report = audit(root, no_sca=True)
            self.assertGreaterEqual(len(report.findings), 2)
            self.assertTrue(report.complete)
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                code = main([str(root), "--no-sca", "--format", "json"])
            self.assertEqual(code, 1)
            self.assertNotIn("A7a9!Bk0PzG3", stdout.getvalue())

    def test_missing_sca_marks_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("aegis_white.sca.shutil.which", return_value=None):
                report = audit(Path(td))
            self.assertFalse(report.complete)
            self.assertEqual(report.checks["sca"], "failed")

    def test_history_catches_deleted_credential(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._git(root, "init", "-q")
            self._git(root, "config", "user.email", "test@example.invalid")
            self._git(root, "config", "user.name", "Example")
            token = "ghp_" + "ZYx8" * 10
            (root / "secret.txt").write_text(token)
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "initial")
            (root / "secret.txt").unlink()
            (root / "clean.txt").write_text("hello")
            self._git(root, "add", "-A")
            self._git(root, "commit", "-qm", "clean")
            current = audit(root, no_sca=True)
            self.assertFalse(any(f.category == "secret" for f in current.findings))
            history = audit(root, history=True, no_sca=True)
            self.assertTrue(any(f.rule_id == "SECRET-GITHUB" and f.path.startswith("git:") for f in history.findings))
            self.assertNotIn(token, render(history, "json"))

    def test_pr_base_only_changed_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            self._git(root, "init", "-q")
            self._git(root, "config", "user.email", "test@example.invalid")
            self._git(root, "config", "user.name", "Example")
            (root / "unchanged.py").write_text("eval(data)\n")  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "base")
            base = self._git(root, "rev-parse", "HEAD")
            (root / "changed.py").write_text("exec(code)\n")  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)
            self._git(root, "add", ".")
            self._git(root, "commit", "-qm", "change")
            self.assertIn("changed.py", changed_paths(root, base))
            result = audit(root, base=base, no_sca=True)
            self.assertEqual([f.path for f in result.findings], ["changed.py"])

    def test_symlinks_are_not_followed(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            (Path(outside) / "evil.py").write_text("eval(data)")  # aegis-white: allow-secret; aegis-white: allow-sast (test fixture)
            try:
                (Path(td) / "ref.py").symlink_to(Path(outside) / "evil.py")
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable")
            self.assertEqual(audit(Path(td), no_sca=True).scanned_files, 0)

    def test_oversize_file_explicit_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "oversize.txt").write_text("A" * 2000)
            result = audit(Path(td), no_sca=True, max_file_bytes=1024)
            self.assertFalse(result.complete)
            self.assertTrue(any("coverage incomplete" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main()
