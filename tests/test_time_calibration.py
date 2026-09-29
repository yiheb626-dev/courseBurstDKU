import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from course_rush_web.core.models import JobConfig, RushSettings
from course_rush_web.services.task_manager import TaskManager


class TimeCalibrationTests(unittest.TestCase):
    def test_defaults_and_round_trip(self):
        settings = RushSettings.from_dict({})
        self.assertTrue(settings.time_sync_enabled)
        self.assertEqual(settings.start_offset_seconds, -0.3)
        config = JobConfig("test", "now", settings)
        self.assertEqual(JobConfig.from_dict(config.to_dict()).settings.start_offset_seconds, -0.3)

    def test_bounds_and_invalid_values(self):
        for value, expected in [(-8, -5), (8, 5), (0, 0), ("NaN", -0.3), ("inf", -0.3), ("bad", -0.3)]:
            self.assertEqual(RushSettings.from_dict({"start_offset_seconds": value}).start_offset_seconds, expected)

    def test_schedule_offsets_and_disabled_ntp(self):
        manager = TaskManager.__new__(TaskManager)
        now = datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
        with patch("course_rush_web.services.task_manager.datetime") as clock:
            clock.fromisoformat.side_effect = datetime.fromisoformat
            clock.now.return_value = now
            for enabled in (True, False):
                for offset in (-5, -0.3, 0, 5):
                    settings = RushSettings(scheduled_start="2026-09-30T12:01:00+00:00", time_sync_enabled=enabled, time_offset_ms=200, start_offset_seconds=offset)
                    self.assertAlmostEqual(manager._delay_until(settings), 60 - 1.5 - (0.2 if enabled else 0) + offset)
            self.assertEqual(manager._delay_until(RushSettings()), 0)
            self.assertEqual(manager._delay_until(RushSettings(scheduled_start="2026-09-30T11:00:00+00:00")), 0)


if __name__ == "__main__":
    unittest.main()
