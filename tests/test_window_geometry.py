"""Headless regression tests for monitor-aware desktop window sizing."""
import unittest

from ots_white.gui import fit_window_to_work_area


class WindowGeometryTests(unittest.TestCase):
    def _assert_inside(self, area):
        geometry, minimum = fit_window_to_work_area(area)
        import re
        match = re.fullmatch(r"(\d+)x(\d+)([+-]\d+)([+-]\d+)", geometry)
        self.assertIsNotNone(match, geometry)
        width, height, x, y = map(int, match.groups())
        left, top, work_width, work_height = area
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
        self.assertGreaterEqual(x, left)
        self.assertGreaterEqual(y, top)
        self.assertLessEqual(x + width, left + work_width)
        self.assertLessEqual(y + height, top + work_height)
        self.assertLessEqual(minimum[0], width)
        self.assertLessEqual(minimum[1], height)
        self.assertLessEqual(width, 1300)
        self.assertLessEqual(height, 800)

    def test_typical_laptop_with_taskbar(self):
        self._assert_inside((0, 0, 1366, 728))

    def test_small_display(self):
        self._assert_inside((0, 0, 1024, 680))

    def test_high_dpi_monitor_with_offset(self):
        self._assert_inside((1920, -120, 2560, 1390))

    def test_negative_monitor_origin(self):
        self._assert_inside((-1600, 0, 1600, 860))

    def test_geometry_is_centered(self):
        value, _ = fit_window_to_work_area((0, 0, 1920, 1040))
        self.assertEqual(value, "1300x800+310+120")

    def test_invalid_area_fails_safely(self):
        with self.assertRaises(ValueError):
            fit_window_to_work_area((0, 0, 0, 600))


if __name__ == "__main__":
    unittest.main()
