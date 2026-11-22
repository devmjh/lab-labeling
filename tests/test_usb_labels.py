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
        for rows in (2, 3, 4):
            self.assertEqual(render_strips(["USB"] * rows, rows=rows, length_mm=15).size, (456, 253))
            with self.assertRaises(ValueError):
                render_strips(["USB"] * (rows+1), rows=rows)
        for kwargs in ({"rows": 5}, {"length_mm": 14}, {"length_mm": 56}):
            with self.assertRaises(ValueError):
                render_strips(["USB"], **kwargs)
        for names in ([], [" "], ["TWO\nLINES"], ["x" * 301]):
            with self.assertRaises(ValueError):
                render_strips(names)

    def test_four_strips_have_three_cut_guides(self):
        label = render_strips(["A", "B", "C", "D"], rows=4)
        # Dashed guide rows sit exactly on the strip boundaries.
        for top in (63, 126, 190):
            self.assertEqual(label.getpixel((0, top)), 0)
            self.assertEqual(label.getpixel((6, top)), 1)

    def test_blank_middle_row_and_fixed_size(self):
        label = render_strips(["32GB", "", "32GB"], length_mm=20, font_px=28)
        self.assertEqual(label.crop((8, 90, 150, 160)).convert("L").getextrema(), (255, 255))
        auto = render_strips(["32GB"], length_mm=20)
        def ink_height(img):
            box = img.crop((0, 6, 150, 78)).convert("L").point(lambda x: 255 - x).getbbox()
            return box[3] - box[1]
        # Fixed 28 px text stays modest; auto-fit grows to fill the strip.
        self.assertLess(ink_height(label), ink_height(auto))

    def test_fixed_size_never_crops(self):
        with self.assertRaises(ValueError):
            render_strips(["UBUNTU SRV 24.04.3"], length_mm=15, font_px=60)
        for px in (9, 121):
            with self.assertRaises(ValueError):
                render_strips(["USB"], font_px=px)
