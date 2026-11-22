import unittest

from labels.print_usb_label import render_strips, to_zpl


class UsbStripTests(unittest.TestCase):
    def test_unused_rows_only_have_cut_guides(self):
        label = render_strips(["UBUNTU SRV 26.04"])
        self.assertEqual(label.size, (456, 253))
        self.assertIsNotNone(label.crop((8, 8, 310, 76)).convert("L").point(lambda x: 255-x).getbbox())
        for top, bottom in ((94, 158), (179, 243)):
            self.assertEqual(label.crop((8, top, 310, bottom)).convert("L").getextrema(), (255, 255))
        zpl = to_zpl(label, copies=1)
        self.assertIn("^LT40\n", zpl)
        self.assertIn("^PQ1\n", zpl)

    def test_both_layouts_fit_names_and_reject_overflow(self):
        for rows in (2, 3):
            self.assertEqual(render_strips(["USB"] * rows, rows=rows, length_mm=15).size, (456, 253))
            with self.assertRaises(ValueError):
                render_strips(["USB"] * (rows+1), rows=rows)
        for kwargs in ({"rows": 4}, {"length_mm": 14}, {"length_mm": 56}):
            with self.assertRaises(ValueError):
                render_strips(["USB"], **kwargs)
        for names in ([], [" "], ["TWO\nLINES"], ["x" * 301]):
            with self.assertRaises(ValueError):
                render_strips(names)
