"""Offline tests for the redacted publication gate."""
import io
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.publication_gate import scan_path, scan_stream


class PublicationGateTests(unittest.TestCase):
    def test_token_shape_in_ascii_and_utf16le(self):
        synthetic = b'ghp_' + b'a' * 32
        for payload in (synthetic, synthetic.decode().encode('utf-16-le')):
            match, size = scan_stream(io.BytesIO(payload))
            self.assertTrue(match)
            self.assertEqual(size, len(payload))

    def test_clean_bytes_are_not_flagged(self):
        found, _ = scan_stream(io.BytesIO(b'local notes and harmless config'))
        self.assertFalse(found)

    def test_archived_member_is_inspected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'sample.zip')
            with zipfile.ZipFile(target, 'w') as z:
                z.writestr('safe.txt', 'harmless')
                z.writestr('other.txt', 'ghp_' + 'a' * 32)
            result = scan_path(target)
            self.assertTrue(result['possible_credentials'])
            self.assertEqual(result['archive_entries'], 2)
            self.assertFalse(result['incomplete'])
            self.assertNotIn('ghp_', str(result))

    def test_nested_archive_is_never_considered_complete(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, 'outer.zip')
            with zipfile.ZipFile(target, 'w') as z:
                z.writestr('nested.zip', b'PK')
            result = scan_path(target)
            self.assertTrue(result['incomplete'])

    def test_bounded_scanning_fails_closed(self):
        with self.assertRaises(ValueError):
            scan_stream(io.BytesIO(b'123456789'), max_bytes=8)


if __name__ == '__main__':
    unittest.main()
