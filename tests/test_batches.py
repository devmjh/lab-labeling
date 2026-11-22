import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from labels import batch_labels as batch


class BatchTests(unittest.TestCase):
    def test_rejects_unsafe_ids_and_duplicate_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "jobs.json"
            for jobs in ([{"id": "../escape", "lines": ["TEXT"]}],
                         [{"id": "same", "lines": ["TEXT"]}] * 2):
                manifest.write_text(json.dumps(jobs))
                with self.assertRaises(ValueError):
                    batch.load_jobs(manifest)

    def test_preview_is_offline_and_repeat_send_is_skipped(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(output_dir=directory, font=batch.printer.FONT,
                                   host="test-printer", port=9100, send=False)
            jobs = [{"id": "one", "lines": ["PARTS", "SENSORS"], "copies": 2}]
            with patch.object(batch.printer.socket, "create_connection") as connect:
                batch.run_batch(jobs, args)
                connect.assert_not_called()
                self.assertTrue(Path(directory, "previews.png").exists())
                args.send = True
                batch.run_batch(jobs, args)
                self.assertEqual(connect.call_count, 1)
                batch.run_batch(jobs, args)
                self.assertEqual(connect.call_count, 1)
                jobs[0]["copies"] = 1
                batch.run_batch(jobs, args)
                self.assertEqual(connect.call_count, 2)

    def test_invalid_later_job_prevents_all_sends(self):
        with tempfile.TemporaryDirectory() as directory:
            args = SimpleNamespace(output_dir=directory, font=batch.printer.FONT,
                                   host="test-printer", port=9100, send=True)
            jobs = [{"id": "one", "lines": ["GOOD"]},
                    {"id": "two", "lines": ["x" * 301]}]
            with patch.object(batch.printer.socket, "create_connection") as connect:
                with self.assertRaises(ValueError):
                    batch.run_batch(jobs, args)
                connect.assert_not_called()
