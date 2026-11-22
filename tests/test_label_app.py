import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.request
import urllib.error

from labels import label_app


class FakeSender:
    def __init__(self, error=None):
        self.calls, self.error = [], error

    def __call__(self, host, port, data):
        self.calls.append((host, port, data))
        if self.error:
            raise self.error


class AppLogicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.sender = FakeSender()
        self.app = label_app.LabelApp(self.tmp.name, sender=self.sender)

    def tearDown(self):
        self.tmp.cleanup()

    def preview(self, job):
        return self.app.preview(job)

    def test_preview_never_connects_and_reports_summary(self):
        with patch.object(label_app.socket, "create_connection") as connect:
            r = self.preview({"kind": "box", "lines": ["ROBOT CAR KIT", "READY TO BUILD"], "copies": 2})
            connect.assert_not_called()
        self.assertEqual((r["width"], r["height"]), (456, 253))
        self.assertIn("2 copies", r["summary"])
        self.assertEqual(len(r["metrics"]), 2)
        self.assertGreater(r["metrics"][0]["height_mm"], r["metrics"][1]["height_mm"])

    def test_usb_summary_counts_blank_rows(self):
        r = self.preview({"kind": "usb", "names": ["WINPE UTIL", "", ""], "rows": 4,
                          "length_mm": 40, "font_px": None, "copies": 1})
        self.assertIn("1 named strip · 3 blank", r["summary"])

    def test_print_requires_matching_fingerprint(self):
        job = {"kind": "bag", "lines": ["ESP32"], "copies": 1}
        status, body = self.app.print_job({"job": job, "fingerprint": "old"})
        self.assertEqual((status, body["code"]), (409, "stale"))
        self.assertEqual(self.sender.calls, [])
        fp = self.preview(job)["fingerprint"]
        status, body = self.app.print_job({"job": job, "fingerprint": fp})
        self.assertEqual((status, body["status"]), (200, "sent"))
        self.assertIn(b"^PQ1", self.sender.calls[0][2])
        self.assertIn(b"^LT40", self.sender.calls[0][2])

    def test_usb_sheets_print_lower_than_box_labels(self):
        for job, lt in (({"kind": "usb", "names": ["A"], "rows": 4, "length_mm": 40,
                          "font_px": None, "copies": 1}, b"^LT50"),
                        ({"kind": "box", "lines": ["A"], "copies": 2}, b"^LT40")):
            fp = self.preview(job)["fingerprint"]
            self.app.print_job({"job": job, "fingerprint": fp})
            self.assertIn(lt, self.sender.calls[-1][2])

    def test_recent_repeat_needs_confirmation(self):
        job = {"kind": "bag", "lines": ["ESP32"], "copies": 1}
        fp = self.preview(job)["fingerprint"]
        self.app.print_job({"job": job, "fingerprint": fp})
        status, body = self.app.print_job({"job": job, "fingerprint": fp})
        self.assertEqual((status, body["code"]), (409, "repeat"))
        self.assertEqual(len(self.sender.calls), 1)
        status, body = self.app.print_job({"job": job, "fingerprint": fp, "confirm_repeat": True})
        self.assertEqual(body["status"], "sent")
        self.assertEqual(len(self.sender.calls), 2)

    def test_outcomes_are_honest(self):
        job = {"kind": "bag", "lines": ["ESP32"], "copies": 1}
        fp = self.preview(job)["fingerprint"]
        self.sender.error = ConnectionError("refused")
        self.assertEqual(self.app.print_job({"job": job, "fingerprint": fp})[1]["status"], "failed")
        self.sender.error = TimeoutError("timed out")
        self.assertEqual(self.app.print_job({"job": job, "fingerprint": fp})[1]["status"], "unknown")
        statuses = [h["status"] for h in self.app.store.read("history", [])]
        self.assertEqual(statuses, ["unknown", "failed"])

    def test_dry_run_writes_zpl_only(self):
        app = label_app.LabelApp(self.tmp.name, dry_run=True, sender=self.sender)
        job = {"kind": "box", "lines": ["PARTS"], "copies": 2}
        entry = app.print_job({"job": job, "fingerprint": app.preview(job)["fingerprint"]})[1]
        self.assertEqual(entry["status"], "dry-run")
        self.assertEqual(self.sender.calls, [])
        self.assertIn("^PQ2", Path(self.tmp.name, "dry-run", entry["id"] + ".zpl").read_text())

    def test_settings_change_invalidates_fingerprint(self):
        job = {"kind": "bag", "lines": ["ESP32"], "copies": 1}
        fp = self.preview(job)["fingerprint"]
        self.app.save_settings({"host": "10.0.0.9", "port": 9100, "offset_mm": 5})
        self.assertEqual(self.app.print_job({"job": job, "fingerprint": fp})[1]["code"], "stale")
        for bad in ({"host": ""}, {"port": 0}, {"offset_mm": 20}):
            with self.assertRaises(ValueError):
                self.app.save_settings(bad)


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = label_app.make_server(label_app.LabelApp(self.tmp.name, sender=FakeSender()), 0)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def post(self, path, body, headers=None):
        req = urllib.request.Request(self.base + path, json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_page_and_preview(self):
        with urllib.request.urlopen(self.base + "/") as r:
            self.assertIn(b"Lab Labels", r.read())
        status, body = self.post("/api/preview", {"kind": "bag", "lines": ["X"]}, {"X-Lab-Labels": "1"})
        self.assertEqual(status, 200)
        self.assertTrue(body["png"])

    def test_cross_site_posts_are_refused(self):
        status, _ = self.post("/api/print", {}, {})
        self.assertEqual(status, 403)
        status, _ = self.post("/api/preview", {"kind": "bag", "lines": ["X"]},
                              {"X-Lab-Labels": "1", "Host": "evil.example"})
        self.assertEqual(status, 403)

    def test_bad_job_is_400(self):
        status, body = self.post("/api/preview", {"kind": "nope"}, {"X-Lab-Labels": "1"})
        self.assertEqual(status, 400)
        self.assertIn("Unknown", body["error"])


if __name__ == "__main__":
    unittest.main()


class FakePhotos:
    def __init__(self, directory):
        from PIL import Image
        self.CACHE = Path(directory) / "cache"
        self.CACHE.mkdir()
        self.fetches = 0
        Image.new("RGB", (300, 400), "red").save(self.CACHE / "a.jpg")
        self.rows = [{"name": "a.jpg", "bytes": (self.CACHE / "a.jpg").stat().st_size,
                      "modified": 0, "arrived": 100.0}]

    def list_rows(self):
        return self.rows

    def fetch(self, row):
        self.fetches += 1
        return self.CACHE / row["name"]


class PhotoInboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.photos = FakePhotos(self.tmp.name)
        self.inbox = label_app.PhotoInbox(self.photos)

    def tearDown(self):
        self.tmp.cleanup()

    def test_thumbnail_is_small_jpeg_and_cached(self):
        data = self.inbox.image("a.jpg", 100)
        self.assertTrue(data.startswith(b"\xff\xd8"))
        from PIL import Image
        import io
        self.assertLessEqual(max(Image.open(io.BytesIO(data)).size), 100)
        self.inbox.image("a.jpg", 100)
        self.assertEqual(self.photos.fetches, 0)  # already in cache, never refetched

    def test_only_inbox_names_are_served(self):
        for name in ("../../etc/passwd", "missing.jpg", "x" * 300):
            with self.assertRaises(ValueError):
                self.inbox.image(name, 100)

    def test_photo_reference_kept_in_job_but_not_fingerprint(self):
        app = label_app.LabelApp(self.tmp.name, sender=FakeSender(), inbox=self.inbox)
        a = app.preview({"kind": "bag", "lines": ["ESP32"], "photo": "a.jpg"})
        b = app.preview({"kind": "bag", "lines": ["ESP32"]})
        self.assertEqual(a["job"]["photo"], "a.jpg")
        self.assertEqual(a["fingerprint"], b["fingerprint"])
