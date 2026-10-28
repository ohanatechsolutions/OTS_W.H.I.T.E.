"""Theme and packaging checks that run headlessly in CI."""
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "ots_white" / "assets"


class DesktopBrandTests(unittest.TestCase):
    def test_gui_python_source_compiles(self):
        source = ROOT / "ots_white" / "gui.py"
        compile(source.read_text(encoding="utf-8"), str(source), "exec")

    def test_png_is_valid_brand_asset(self):
        data = (ASSETS / "ots_white_logo.png").read_bytes()
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(data), 100)

    def test_ico_contains_windows_icon_resource(self):
        data = (ASSETS / "ots_white.ico").read_bytes()
        self.assertGreater(len(data), 100)
        reserved, kind, count = struct.unpack_from("<HHH", data)
        self.assertEqual((reserved, kind), (0, 1))
        self.assertGreaterEqual(count, 1)
        size, offset = struct.unpack_from("<II", data, 14)
        self.assertLessEqual(size + offset, len(data))
        self.assertTrue(data[offset:offset + 8] == b"\x89PNG\r\n\x1a\n" or
                        data[offset:offset + 4] == b"\x28\x00\x00\x00")

    def test_windows_build_embeds_both_assets(self):
        workflow = (ROOT / ".github" / "workflows" / "windows-installer.yml").read_text(
            encoding="utf-8")
        self.assertIn('--icon "ots_white/assets/ots_white.ico"', workflow)
        self.assertIn("--add-data", workflow)
        self.assertIn("ots_white/assets;ots_white/assets", workflow)
        installer = (ROOT / "installer" / "OTS_WHITE.iss").read_text(encoding="utf-8")
        self.assertIn("SetupIconFile=", installer)


if __name__ == "__main__":
    unittest.main()
