import importlib.util
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch


@unittest.skipUnless(sys.platform.startswith("linux"), "Retention runs on Linux")
class RetentionTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "retention", Path(__file__).resolve().parents[1] / "lab-photos/retention.py")
        self.retention = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.retention)

    def test_recent_files_protected_even_over_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            photo = root / "inbox/photo.jpg"
            photo.write_bytes(b"photo")
            with patch.object(self.retention, "MAX_BYTES", 1):
                self.retention.clean(root, now=time.time())
            self.assertTrue(photo.exists())

    def test_expiry_only_removes_inbox_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            photo = root / "inbox/photo.jpg"
            photo.write_bytes(b"photo")
            outside = root / "keep.txt"
            outside.write_text("keep")
            self.retention.clean(root, now=time.time() + 15 * 86400)
            self.assertFalse(photo.exists())
            self.assertTrue(outside.exists())

    def test_old_eligible_files_pruned_over_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "inbox").mkdir()
            (root / "inbox/photo.jpg").write_bytes(b"photo")
            with patch.object(self.retention, "MAX_BYTES", 1):
                result = self.retention.clean(root, now=time.time() + 7200)
            self.assertEqual(result["files_deleted"], 1)


if __name__ == "__main__":
    unittest.main()
