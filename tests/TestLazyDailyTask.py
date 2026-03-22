import subprocess
import unittest

from src.task.schedule_utils import (
    build_create_daily_task_command,
    build_delete_task_command,
    build_windows_launch_command,
    normalize_daily_time,
)


class TestLazyDailyTask(unittest.TestCase):

    def test_normalize_daily_time(self):
        self.assertEqual(normalize_daily_time("6:5"), "06:05")
        self.assertEqual(normalize_daily_time("23:30"), "23:30")

    def test_normalize_daily_time_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            normalize_daily_time("24:00")
        with self.assertRaises(ValueError):
            normalize_daily_time("abc")

    def test_build_windows_launch_command_for_source_mode(self):
        command = build_windows_launch_command(
            1,
            True,
            python_executable=r"C:\Python312\python.exe",
            main_script=r"D:\ok-ww\main.py",
            frozen=False,
        )
        expected = subprocess.list2cmdline([
            r"C:\Python312\python.exe",
            r"D:\ok-ww\main.py",
            "-t",
            "1",
            "-e",
        ])
        self.assertEqual(command, expected)

    def test_build_windows_launch_command_for_frozen_mode(self):
        command = build_windows_launch_command(
            3,
            False,
            executable=r"D:\ok-ww\ok-ww.exe",
            frozen=True,
        )
        expected = subprocess.list2cmdline([
            r"D:\ok-ww\ok-ww.exe",
            "-t",
            "3",
        ])
        self.assertEqual(command, expected)

    def test_build_create_and_delete_commands(self):
        create_command = build_create_daily_task_command(
            "OK-WW Daily Auto Start",
            "06:00",
            r"\"D:\ok-ww\ok-ww.exe\" -t 1 -e",
        )
        self.assertEqual(create_command[0], "schtasks")
        self.assertIn("/Create", create_command)
        self.assertIn("/TR", create_command)
        self.assertIn("/ST", create_command)
        self.assertIn("06:00", create_command)

        delete_command = build_delete_task_command("OK-WW Daily Auto Start")
        self.assertEqual(delete_command, ["schtasks", "/Delete", "/TN", "OK-WW Daily Auto Start", "/F"])


if __name__ == '__main__':
    unittest.main()
