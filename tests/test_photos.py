import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "photos", Path(__file__).resolve().parents[1] / "lab-photos/photos.py")
photos = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(photos)

OLD = {"name": "old.jpg", "bytes": 10, "modified": 0, "arrived": 1000.0}
NEW = {"name": "new.jpg", "bytes": 10, "modified": 0, "arrived": 2000.0}


class PhotoTests(unittest.TestCase):
    def test_latest_refuses_stale_photo(self):
        with patch.object(photos, "list_rows", return_value=[OLD]), \
             patch.object(photos, "server_now", return_value=1000.0 + 31 * 60), \
             patch.object(photos, "fetch") as fetch:
            with self.assertRaises(photos.PhotoError):
                photos.latest(max_age_min=30)
            fetch.assert_not_called()
            photos.latest()
            fetch.assert_called_once_with(OLD)

    def test_wait_ignores_existing_and_returns_new(self):
        rows = iter([[OLD], [OLD], [NEW, OLD], [NEW, OLD]])
        with patch.object(photos, "list_rows", side_effect=lambda: next(rows)), \
             patch.object(photos, "server_now", return_value=1500.0), \
             patch.object(photos, "fetch", side_effect=lambda r: r["name"]):
            self.assertEqual(photos.wait(timeout=60, sleep=lambda s: None, clock=lambda: 0), "new.jpg")

    def test_wait_times_out(self):
        ticks = iter(range(0, 1000, 10))
        with patch.object(photos, "list_rows", return_value=[OLD]), \
             patch.object(photos, "server_now", return_value=1500.0):
            with self.assertRaises(photos.PhotoError):
                photos.wait(timeout=30, sleep=lambda s: None, clock=lambda: next(ticks))

    def test_ssh_failure_is_friendly(self):
        import subprocess
        with patch.object(photos.subprocess, "run", side_effect=subprocess.CalledProcessError(255, "ssh")):
            with self.assertRaisesRegex(photos.PhotoError, "Could not reach"):
                photos.list_rows()
