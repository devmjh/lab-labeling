import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "labels", Path(__file__).resolve().parents[1] / "labels/print_box_label.py")
labels = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(labels)


class LabelTests(unittest.TestCase):
    def test_raster_and_copy_count(self):
        from PIL import Image
        label = Image.new("1", (456, 253), 1)
        label.putpixel((0, 0), 0)
        zpl = labels.to_zpl(label, copies=2)
        self.assertIn("^LT40\n", zpl)
        self.assertIn("^PQ2\n", zpl)
        self.assertIn("^GFA,14421,14421,57,80", zpl)

    def test_invalid_copies_rejected(self):
        from PIL import Image
        for copies in (0, -1, 101, 1.5):
            with self.subTest(copies=copies), self.assertRaises(ValueError):
                labels.to_zpl(Image.new("1", (456, 253)), copies=copies)

    def test_short_detail_does_not_dominate(self):
        label = labels.render_label(["HARD DRIVE PARTS", "MAGNETS / MOTOR SCREWS", "ARMS"])
        rows = [y for y in range(label.height)
                if min(label.crop((0, y, label.width, y + 1)).get_flattened_data()) == 0]
        groups = []
        for y in rows:
            if not groups or y != groups[-1][-1] + 1:
                groups.append([])
            groups[-1].append(y)
        self.assertEqual(len(groups), 3)
        self.assertLessEqual(len(groups[2]), len(groups[1]) + 1)
        self.assertGreater(groups[0][0], 0)
        self.assertLess(groups[-1][-1], 252)

    def test_preview_never_connects(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(width=456, height=253, margin=8, border=False,
                font=labels.FONT, offset_mm=5, copies=2, output=str(Path(tmp) / "label"),
                host="unused", port=9100)
            with patch.object(labels.socket, "create_connection") as connect:
                labels.save_and_send(["TEST"], args, send=False)
                connect.assert_not_called()
            self.assertTrue(Path(tmp, "label.png").is_file())
            self.assertIn("^PQ2", Path(tmp, "label.zpl").read_text())


if __name__ == "__main__":
    unittest.main()
